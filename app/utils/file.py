"""Filesystem and JSONL helper utilities for path resolution and reading/writing line-delimited JSON."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List


def get_project_root() -> Path:
    """Return the current working directory as the project root."""
    return Path(os.getcwd()).resolve()


def get_abs_path(path: str) -> Path:
    """Resolve a path relative to the project root into an absolute path."""
    return get_project_root() / path


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    """Read a JSONL file and return its records as a list of dicts."""
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def write_list_to_jsonl(meta_list, out_path):
    """Write a list of dict-like items to a JSONL file, creating parent directories as needed."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        for item in meta_list:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def jsonl_to_dict(path: str, key_field: str) -> dict:
    """Read a JSONL file into a dict keyed by the given field's value from each record."""
    out = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            k = obj.get(key_field)
            if k is None:
                continue
            out[k] = obj
    return out

def count_subdirectories():
    """Read paths from files.txt and count immediate child directories under each parent directory."""
    subdirs = {}  # parent_dir -> set(child_dirs)

    with open("files.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # supports: File: docs-main\content\...
            if line.lower().startswith("file:"):
                path_str = line.split(":", 1)[1].strip()
            else:
                path_str = line

            parts = Path(path_str).parts
            folders = parts[:-1]  # ignore filename

            # count parent -> child directory relationship
            for i in range(len(folders) - 1):
                parent = str(Path(*folders[: i + 1]))
                child = folders[i + 1]
                subdirs.setdefault(parent, set()).add(child)

    # final counts
    return {parent: len(children) for parent, children in subdirs.items()}
