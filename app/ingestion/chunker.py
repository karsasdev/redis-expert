"""Loads Redis markdown documentation from disk and splits it into chunks for embedding/indexing."""

import re

from langchain_community.document_loaders import TextLoader

from app.config import settings
from app.utils.file import get_abs_path


class DocumentChunker:

    def __init__(self, splitter):
        """Store the text splitter used to break documents into chunks."""
        self.splitter = splitter

    def doc_to_chunks(self, only_meta: bool = False):
        """Load all non-versioned, non-release-notes markdown docs and split them into chunks."""
        knowledge_base_path = get_abs_path(settings.MD_DOCS_PATH)
        files = sorted(knowledge_base_path.rglob("*.md"))
        def is_version(s: str) -> bool:
            """Check whether a string contains a version-like number (e.g. 7.2 or 7.2.1)."""
            return bool(re.search(r"\b\d+\.\d+(?:\.\d+)?\b", s))

        documents = []
        metadata_all = []
        for file in files:
            if is_version(str(file.absolute())) or "release-notes" in str(file.absolute()):
                continue
            docs = TextLoader(str(file), encoding="utf-8").load()

            documents.extend(docs)
        if only_meta:
            return metadata_all

        return self.splitter.split_documents(documents)


    @staticmethod
    def get_entire_documentation() -> str:
        """Concatenate the contents of every markdown doc file into a single string."""
        knowledge_base_path = get_abs_path(settings.MD_DOCS_PATH)

        files = sorted(knowledge_base_path.rglob("*.md"))
        print(f"Found {len(files)} files in the knowledge base")

        entire_knowledge_base = ""
        for file_path in files:
            entire_knowledge_base += file_path.read_text(encoding="utf-8")
            entire_knowledge_base += "\n\n"

        return entire_knowledge_base
