"""Filesystem and JSONL helper utilities for path resolution and reading/writing line-delimited JSON."""

import json
import os
from pathlib import Path


def get_project_root() -> Path:
    """Return the current working directory as the project root."""
    return Path(os.getcwd()).resolve()


def get_abs_path(path: str) -> Path:
    """Resolve a path relative to the project root into an absolute path."""
    return get_project_root() / path


def write_list_to_jsonl(meta_list, out_path):
    """Write a list of dict-like items to a JSONL file, creating parent directories as needed."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        for item in meta_list:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
