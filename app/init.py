"""Application bootstrap helpers: downloading Redis docs, initializing the vector DB, and launching the Gradio UI."""

import random
import shutil
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

import gradio as gr
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ragas.testset import TestsetGenerator

from app.config import settings
from app.embeddings import get_embeddings
from app.ingestion.chunker import DocumentChunker
from app.store.pg_vector_async_store import PGVectorAsyncStore
from app.utils.file import get_abs_path, write_list_to_jsonl

REDIS_DOCS_URL = "https://github.com/redis/docs/archive/refs/heads/main.zip"


def _download_zip(url: str, zip_path: Path) -> None:
    """Download a URL to the given zip file path, creating parent directories as needed."""
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading: {url}")
    urlretrieve(url, zip_path)
    print(f"Saved: {zip_path}")


def _extract_zip(zip_path: Path, out_dir: Path, clean_out_dir: bool = True) -> None:
    """Extract a zip archive into out_dir, optionally clearing it first."""
    if clean_out_dir and out_dir.exists():
        shutil.rmtree(out_dir)

    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Extracting: {zip_path} -> {out_dir}")

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(out_dir)


def _keep_only_md_files(root_dir: Path) -> tuple[int, int]:
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


def _remove_empty_dirs(root_dir: Path) -> int:
    """Recursively remove empty directories under root_dir, returning the count removed."""
    removed = 0
    for p in sorted(root_dir.rglob("*"), reverse=True):
        if p.is_dir() and not any(p.iterdir()):
            p.rmdir()
            removed += 1
    return removed


def initialize_redis_docs():
    """Download, extract, and clean the Redis docs archive into the configured docs path, if not already present."""
    out_dir = get_abs_path(settings.MD_DOCS_PATH)
    if out_dir.exists() and out_dir.is_dir():
        print("Redis docs already exists. Skipping download.")
        return

    zip_path = out_dir.with_suffix(".zip")

    _download_zip(REDIS_DOCS_URL, zip_path)
    _extract_zip(zip_path, out_dir)

    kept, deleted = _keep_only_md_files(out_dir)
    _remove_empty_dirs(out_dir)

    zip_path.unlink(missing_ok=True)

    print(f"Final .md files: {kept}")
    print("Done.")


def initialize_vector_database(by_reset: bool = False):
    """Chunk and embed the Redis docs into the vector store, unless already initialized (or forced via reset)."""
    vs = PGVectorAsyncStore(embeddings=get_embeddings())
    if by_reset:
        print("Deleting existing vectorstore...")
        vs.delete()
    elif vs.count() > 0:
        print("Vector DB already initialized. Skipping.")
        return

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunker = DocumentChunker(splitter=splitter)
    chunks = chunker.doc_to_chunks()
    vs.add(chunks)
    print(f"Vector database initialization complete - chunks added: {len(chunks)}")


def initialize_ground_truth_dataset(
    output_path: str = "app/evals/dataset.jsonl",
    sample_size: int = 800,
    testset_size: int = 200,
    seed: int = 42,
):
    """Generate a synthetic Q&A eval dataset from the Redis docs via Ragas, unless it already exists."""
    if Path(output_path).exists():
        print("Ground truth dataset already exists. Skipping.")
        return

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = DocumentChunker(splitter=splitter).doc_to_chunks()

    random.seed(seed)
    sample = random.sample(chunks, min(sample_size, len(chunks)))
    print(f"Loaded {len(chunks)} doc chunks, sampled {len(sample)} for knowledge-graph generation")

    generator = TestsetGenerator.from_langchain(
        llm=ChatOpenAI(model=settings.LLM_MODEL),
        embedding_model=get_embeddings(),
    )
    testset = generator.generate_with_langchain_docs(sample, testset_size=testset_size)

    rows = testset.to_list()
    write_list_to_jsonl(rows, output_path)
    print(f"Wrote {len(rows)} generated Q&A pairs to {output_path}")


def initialize_gradio_app(chat_func, title: str = "Chat with RedisAI", inbrowser: bool = True):
    """Build and launch the Gradio chat interface backed by the given chat function."""
    CSS = """
#chatbot {
  height: 75vh !important;
  overflow: auto;
}
"""
    with gr.Blocks(css=CSS) as demo:
        gr.Markdown(f"# {title}")
        gr.ChatInterface(
            fn=chat_func,
            chatbot=gr.Chatbot(elem_id="chatbot"),
        )
        demo.launch(
            server_name=settings.GRADIO_SERVER_NAME,
            server_port=int(settings.GRADIO_SERVER_PORT),
            inbrowser=True,
        )
    return demo
