"""Run Ragas metrics against the chatbot using the generated ground-truth dataset."""

import csv
import json
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from ragas import evaluate
from ragas.dataset_schema import EvaluationDataset, SingleTurnSample
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import ContextUtilization, Faithfulness, LLMContextRecall, ResponseRelevancy
from ragas.run_config import RunConfig

from app.chatbot.openai import ChatBot
from app.config import settings
from app.embeddings import get_embeddings
from app.prompts.system import SYSTEM_PROMPT
from app.store.pg_vector import PGVectorStore

DATASET_PATH = "app/evals/dataset.jsonl"
SCORES_PATH = "app/evals/results.json"
OBSERVATIONS_PATH = "app/evals/results.csv"


def load_dataset(path: str) -> list[dict]:
    """Read a JSONL ground-truth dataset into a list of row dicts."""
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def answer_question(vs: PGVectorStore, bot: ChatBot, question: str) -> tuple[list[str], str]:
    """Retrieve context and generate an answer for one question, exactly as the live app does."""
    chunks = vs.get(question)
    contexts = [c.page_content for c in chunks]
    system_message = SystemMessage(content=SYSTEM_PROMPT.format(context="\n\n".join(contexts)))
    answer = bot.generate(system_message, HumanMessage(content=question))
    return contexts, answer


def score_summary(df) -> dict[str, float]:
    """Mean each metric column, ignoring rows where Ragas failed to score them."""
    metric_cols = [c for c in ("faithfulness", "answer_relevancy", "context_utilization", "context_recall") if c in df.columns]
    return {col: round(df[col].dropna().mean(), 3) for col in metric_cols}


def build_observations(scores: dict[str, float], n_samples: int) -> list[str]:
    """Summarize the eval run in 3-4 plain-language lines instead of dumping raw per-row data."""
    strongest = max(scores, key=scores.get)
    weakest = min(scores, key=scores.get)
    lines = [
        f"Evaluated {n_samples} questions across: {', '.join(scores)}.",
        f"Strongest signal: {strongest} ({scores[strongest]:.2f}).",
        f"Weakest signal: {weakest} ({scores[weakest]:.2f}) — look here first for improvements.",
    ]
    if weakest == "context_utilization":
        lines.append("Low context_utilization points at retrieval, not generation, as the bottleneck.")
    elif weakest in ("faithfulness",):
        lines.append("Low faithfulness suggests answers are drifting from the retrieved context.")
    return lines


def main():
    load_dotenv(override=True)
    rows = load_dataset(DATASET_PATH)
    print(f"Loaded {len(rows)} ground-truth rows from {DATASET_PATH}")

    vs = PGVectorStore(embeddings=get_embeddings())
    bot = ChatBot(vs)

    samples = []
    for i, row in enumerate(rows, start=1):
        question = row["user_input"]
        contexts, answer = answer_question(vs, bot, question)
        samples.append(
            SingleTurnSample(
                user_input=question,
                retrieved_contexts=contexts,
                response=answer,
                reference=row.get("reference"),
            )
        )
        print(f"[{i}/{len(rows)}] answered: {question[:60]}")

    dataset = EvaluationDataset(samples=samples)

    ragas_llm = LangchainLLMWrapper(ChatOpenAI(model=settings.LLM_MODEL))
    ragas_embeddings = LangchainEmbeddingsWrapper(get_embeddings())

    metrics = [Faithfulness(), ResponseRelevancy(), ContextUtilization()]
    if any(s.reference for s in samples):
        metrics.append(LLMContextRecall())

    # Lower concurrency + longer timeout: the default (max_workers=16, timeout=180) floods
    # OpenAI with parallel calls, causing throttled requests to time out instead of fail fast.
    run_config = RunConfig(max_workers=4, timeout=300)
    result = evaluate(
        dataset, metrics=metrics, llm=ragas_llm, embeddings=ragas_embeddings, run_config=run_config
    )
    df = result.to_pandas()
    scores = score_summary(df)

    Path(SCORES_PATH).parent.mkdir(parents=True, exist_ok=True)
    with open(SCORES_PATH, "w", encoding="utf-8") as f:
        json.dump({"n_samples": len(df), **scores}, f, indent=2)

    with open(OBSERVATIONS_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["observation"])
        for line in build_observations(scores, len(df)):
            writer.writerow([line])

    print(result)
    print(f"Wrote scores to {SCORES_PATH}")
    print(f"Wrote observations to {OBSERVATIONS_PATH}")


if __name__ == "__main__":
    main()
