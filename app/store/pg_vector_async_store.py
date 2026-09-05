"""PGVectorStore variant that embeds document chunks across multiple worker processes."""

import os
from concurrent.futures import ProcessPoolExecutor

from app.config import settings
from app.store.pg_vector import PGVectorStore
from app.utils.decorators import time_it

_worker_model = None


def _init_worker(model_name: str, encode_kwargs: dict) -> None:
    """Load the embedding model once per worker process, reused across every batch it handles."""
    import torch
    from langchain_huggingface import HuggingFaceEmbeddings

    global _worker_model
    torch.set_num_threads(1)  # each worker runs independently; avoid fanning out to all cores
    _worker_model = HuggingFaceEmbeddings(model_name=model_name, encode_kwargs=encode_kwargs)


def _embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts using the worker-local model loaded by `_init_worker`."""
    return _worker_model.embed_documents(texts)


class PGVectorAsyncStore(PGVectorStore):
    @time_it
    def add(self, chunks, max_workers: int | None = None):
        """Embed document chunks in parallel worker processes, then insert them into the store in batches."""
        max_workers = max_workers or os.cpu_count()
        embedding_model = self.store.embedding_function
        model_name = embedding_model.model_name
        encode_kwargs = embedding_model.encode_kwargs

        text_batches = [
            [c.page_content for c in chunks[i : i + settings.CHUNKS_BATCH_SIZE]]
            for i in range(0, len(chunks), settings.CHUNKS_BATCH_SIZE)
        ]
        meta_batches = [
            [c.metadata for c in chunks[i : i + settings.CHUNKS_BATCH_SIZE]]
            for i in range(0, len(chunks), settings.CHUNKS_BATCH_SIZE)
        ]

        inserted = 0
        with ProcessPoolExecutor(
            max_workers=max_workers, initializer=_init_worker, initargs=(model_name, encode_kwargs)
        ) as pool:
            for text_batch, meta_batch, embeddings in zip(
                text_batches, meta_batches, pool.map(_embed_batch, text_batches)
            ):
                self.store.add_embeddings(texts=text_batch, embeddings=embeddings, metadatas=meta_batch)
                inserted += len(text_batch)
                print(f"Inserted {inserted} / {len(chunks)} chunks")
        print("Inserted all chunks")
