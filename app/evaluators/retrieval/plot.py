import matplotlib.pyplot as plt
from pathlib import Path

from app.utils import get_abs_path


# ---------------------------
# Helpers
# ---------------------------
def _short(s: str, n: int = 70) -> str:
    s = (s or "").strip()
    return s[:n] + ("..." if len(s) > n else "")


def _rows(results: list[dict]) -> list[dict]:
    """
    Input format expected:
    results = [
      {
        "id": "...",
        "question": "...",
        "metrics": {
            "hit": 1.0,
            "mrr": 0.5,
            "ndcg": 0.7,
            "retrieved_count": 10,
            "relevant_count": 3,
            "keyword_coverage": 66.6,
            ...
        }
      },
      ...
    ]
    """
    rows = []
    for r in results:
        m = r.get("metrics", {})
        rows.append(
            {
                "id": r.get("id", ""),
                "short_id": (r.get("id", "")[:6] if r.get("id") else "??????"),
                "question": r.get("question", ""),
                "label": f"{(r.get('id','')[:6] if r.get('id') else '??????')} | {_short(r.get('question',''), 80)}",
                "hit": float(m.get("hit", 0.0)),
                "mrr": float(m.get("mrr", 0.0)),
                "ndcg": float(m.get("ndcg", 0.0)),
                "keyword_coverage": float(m.get("keyword_coverage", 0.0)),  # 0..100
                "retrieved_count": float(m.get("retrieved_count", 0.0)),
                "relevant_count": float(m.get("relevant_count", 0.0)),
            }
        )
    return rows


def _save_or_show(save_path: str | None, dpi: int = 200, show: bool = True):
    if save_path:
        p = Path(save_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(str(p), dpi=dpi, bbox_inches="tight")
        print(f"Saved: {p}")
    if show:
        plt.show()
    else:
        plt.close()


# ---------------------------
# Summary
# ---------------------------
def print_retrieval_summary(results: list[dict]):
    rows = _rows(results)
    total = len(rows)

    if total == 0:
        print("No results to summarize.")
        return

    hit_rate = sum(r["hit"] for r in rows) / total
    avg_mrr = sum(r["mrr"] for r in rows) / total
    avg_ndcg = sum(r["ndcg"] for r in rows) / total
    avg_kwcov = sum(r["keyword_coverage"] for r in rows) / total

    hit_0 = sum(1 for r in rows if r["hit"] == 0.0)
    mrr_lt_033 = sum(1 for r in rows if r["mrr"] < 0.33) / total * 100
    mrr_lt_02 = sum(1 for r in rows if r["mrr"] < 0.20) / total * 100
    ndcg_lt_05 = sum(1 for r in rows if r["ndcg"] < 0.50) / total * 100

    print("========== Retrieval Summary ==========")
    print(f"Total Questions        : {total}")
    print(f"Hit@K rate             : {hit_rate:.3f}")
    print(f"Avg MRR                : {avg_mrr:.3f}")
    print(f"Avg NDCG               : {avg_ndcg:.3f}")
    print(f"Avg keyword coverage   : {avg_kwcov:.1f}%")
    print("--------------------------------------")
    print(f"Hit=0 count            : {hit_0}")
    print(f"MRR < 0.33             : {mrr_lt_033:.1f}%")
    print(f"MRR < 0.20             : {mrr_lt_02:.1f}%")
    print(f"NDCG < 0.50            : {ndcg_lt_05:.1f}%")
    print("======================================")

    if hit_0 > 0:
        print("\nHit=0 Questions (first 20):")
        for r in [x for x in rows if x["hit"] == 0.0][:20]:
            print(f"- {r['short_id']} | {r['question']}")


# ---------------------------
# Plots (Readable for 200+)
# ---------------------------
def plot_scatter_mrr_ndcg(
        results: list[dict],
        title: str = "NDCG vs MRR",
        save_path: str | None = None,
        dpi: int = 200,
        show: bool = True,
):
    rows = _rows(results)
    x = [r["mrr"] for r in rows]
    y = [r["ndcg"] for r in rows]

    plt.figure(figsize=(7, 6))
    plt.scatter(x, y, alpha=0.7)

    plt.title(title)
    plt.xlabel("MRR")
    plt.ylabel("NDCG")
    plt.xlim(-0.02, 1.05)
    plt.ylim(-0.02, 1.05)
    plt.grid(True, linestyle="--", linewidth=0.7)
    plt.tight_layout()

    _save_or_show(save_path, dpi=dpi, show=show)


def plot_histograms(
        results: list[dict],
        bins: int = 12,
        title: str = "Metric Distributions",
        save_path: str | None = None,
        dpi: int = 200,
        show: bool = True,
):
    rows = _rows(results)

    hit = [r["hit"] for r in rows]
    mrr = [r["mrr"] for r in rows]
    ndcg = [r["ndcg"] for r in rows]
    kwcov_scaled = [r["keyword_coverage"] / 100.0 for r in rows]

    plt.figure(figsize=(12, 5))
    plt.hist(hit, bins=bins, alpha=0.6, label="Hit@K")
    plt.hist(mrr, bins=bins, alpha=0.6, label="MRR")
    plt.hist(ndcg, bins=bins, alpha=0.6, label="NDCG")
    plt.hist(kwcov_scaled, bins=bins, alpha=0.6, label="Keyword Coverage (scaled)")

    plt.title(title)
    plt.xlabel("Score")
    plt.ylabel("Count")
    plt.xlim(0.0, 1.05)
    plt.grid(True, linestyle="--", linewidth=0.7)
    plt.legend()
    plt.tight_layout()

    _save_or_show(save_path, dpi=dpi, show=show)


def plot_worst_best(
        results: list[dict],
        metric: str = "mrr",
        n: int = 25,
        save_path_worst: str | None = None,
        save_path_best: str | None = None,
        dpi: int = 200,
        show: bool = True,
):
    """
    metric: "mrr" or "ndcg"
    plots worst N and best N as separate graphs
    """
    if metric not in {"mrr", "ndcg"}:
        raise ValueError("metric must be 'mrr' or 'ndcg'")

    rows = _rows(results)
    rows.sort(key=lambda x: x[metric])

    worst = rows[:n]
    best = rows[-n:]

    def _barh_plot(items: list[dict], title: str, save_path: str | None):
        labels = [r["label"] for r in items]
        vals = [r[metric] for r in items]
        y = list(range(len(items)))

        plt.figure(figsize=(14, max(6, 0.42 * len(items))))
        plt.barh(y, vals)
        plt.yticks(y, labels)
        plt.xlim(0.0, 1.05)
        plt.xlabel(metric.upper())
        plt.title(title)
        plt.grid(True, axis="x", linestyle="--", linewidth=0.7)
        plt.tight_layout()
        _save_or_show(save_path, dpi=dpi, show=show)

    _barh_plot(worst, f"Worst {n} by {metric.upper()}", save_path_worst)
    _barh_plot(best, f"Best {n} by {metric.upper()}", save_path_best)


def plot_failures_hit0(
        results: list[dict],
        max_items: int = 40,
        save_path: str | None = None,
        dpi: int = 200,
        show: bool = True,
):
    rows = _rows(results)
    fails = [r for r in rows if r["hit"] == 0.0]

    if not fails:
        # still produce a simple "no failures" plot
        plt.figure(figsize=(10, 2))
        plt.title("Hit=0 Failures (none 🎉)")
        plt.xlim(0, 1)
        plt.yticks([])
        plt.xticks([])
        plt.tight_layout()
        _save_or_show(save_path, dpi=dpi, show=show)
        return

    fails = fails[:max_items]
    labels = [r["label"] for r in fails]
    vals = [r["hit"] for r in fails]
    y = list(range(len(fails)))

    plt.figure(figsize=(14, max(4, 0.45 * len(fails))))
    plt.barh(y, vals)
    plt.yticks(y, labels)
    plt.xlim(0.0, 1.05)
    plt.xlabel("HIT")
    plt.title(f"Hit=0 Failures (showing {len(fails)})")
    plt.grid(True, axis="x", linestyle="--", linewidth=0.7)
    plt.tight_layout()

    _save_or_show(save_path, dpi=dpi, show=show)


# ---------------------------
# One-shot report generator
# ---------------------------
def generate_retrieval_report(
        results: list[dict],
        out_dir: str = "plots",
        n: int = 25,
        dpi: int = 200,
        show: bool = False,
):
    out_dir = get_abs_path(out_dir)
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    print_retrieval_summary(results)

    plot_scatter_mrr_ndcg(
        results,
        title="NDCG vs MRR (no labels)",
        save_path=f"{out_dir}/01_scatter_mrr_ndcg.png",
        dpi=dpi,
        show=show,
    )

    plot_histograms(
        results,
        save_path=f"{out_dir}/02_histograms.png",
        dpi=dpi,
        show=show,
    )

    plot_worst_best(
        results,
        metric="mrr",
        n=n,
        save_path_worst=f"{out_dir}/03_worst_{n}_mrr.png",
        save_path_best=f"{out_dir}/04_best_{n}_mrr.png",
        dpi=dpi,
        show=show,
    )

    plot_worst_best(
        results,
        metric="ndcg",
        n=n,
        save_path_worst=f"{out_dir}/05_worst_{n}_ndcg.png",
        save_path_best=f"{out_dir}/06_best_{n}_ndcg.png",
        dpi=dpi,
        show=show,
    )

    plot_failures_hit0(
        results,
        save_path=f"{out_dir}/07_hit0_failures.png",
        dpi=dpi,
        show=show,
    )

    print(f"\n✅ Report saved under folder: {out_dir}")
