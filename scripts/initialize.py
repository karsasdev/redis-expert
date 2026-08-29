"""Downloads the Redis docs archive, extracts it, and keeps only markdown files for ingestion."""

import shutil
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

from app.config import settings
from app.utils.file import get_abs_path

URL = "https://github.com/redis/docs/archive/refs/heads/main.zip"


def download_zip(url: str, zip_path: Path) -> None:
    """Download a URL to the given zip file path, creating parent directories as needed."""
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading: {url}")
    urlretrieve(url, zip_path)
    print(f"Saved: {zip_path}")


def extract_zip(zip_path: Path, out_dir: Path, clean_out_dir: bool = True) -> None:
    """Extract a zip archive into out_dir, optionally clearing it first."""
    if clean_out_dir and out_dir.exists():
        shutil.rmtree(out_dir)

    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Extracting: {zip_path} -> {out_dir}")

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(out_dir)


def keep_only_md_files(root_dir: Path) -> tuple[int, int]:
    """Recursively delete all non-markdown files under root_dir, returning (kept, deleted) counts."""
    deleted = 0
    kept = 0

    for p in root_dir.rglob("*"):
        if p.is_file():
            if p.suffix.lower() == ".md":
                kept += 1
            else:
                p.unlink()
                deleted += 1

    return kept, deleted


def remove_empty_dirs(root_dir: Path) -> int:
    """Recursively remove empty directories under root_dir, returning the count removed."""
    removed = 0
    for p in sorted(root_dir.rglob("*"), reverse=True):
        if p.is_dir() and not any(p.iterdir()):
            p.rmdir()
            removed += 1
    return removed


def cleanup_zip(zip_path: Path) -> None:
    """Delete the downloaded zip file if it exists."""
    zip_path.unlink(missing_ok=True)

def download_redis_docs() -> None:
    """Download, extract, and clean the Redis docs archive into the configured docs path, if not already present."""
    out_dir = get_abs_path(settings.MD_DOCS_PATH)
    if is_redis_docs_exists(out_dir):
        print("Redis docs already exists. Skipping download.")
        return

    zip_path = out_dir.with_suffix(".zip")

    download_zip(URL, zip_path)
    extract_zip(zip_path, out_dir)

    kept, deleted = keep_only_md_files(out_dir)
    remove_empty_dirs(out_dir)

    cleanup_zip(zip_path)

    print(f"Final .md files: {kept}")
    print("Done.")

def setup() -> None:
    """Entry point for running the docs download as a standalone script."""
    download_redis_docs()


def is_redis_docs_exists(docs_dir: Path) -> bool:
    """Check whether the docs directory already exists."""
    return docs_dir.exists() and docs_dir.is_dir()


if __name__ == "__main__":
    setup()
