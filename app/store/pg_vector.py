"""Postgres-backed vector store wrapper (via langchain_postgres) for storing and retrieving document embeddings."""

from langchain_postgres import PGVector

from app.config import settings
from app.utils.decorators import time_it


class PGVectorStore:
    def __init__(self, embeddings):
        """Connect to the Postgres vector collection using the given embeddings model."""
        self.store = PGVector(
            connection=settings.POSTGRES_DB_URI,
            embeddings=embeddings,
            collection_name=settings.COLLECTION_NAME,
            use_jsonb=True,
        )

    def get(self, query: str):
        """Return the most similar document chunks to the query."""
        return self.store.similarity_search(query, k=settings.CHUNK_RETRIVAL_SIZE)

    def count(self) -> int:
        """Return the number of embeddings currently stored in the collection."""
        with self.store._make_sync_session() as session:
            collection = self.store.get_collection(session)
            if collection is None:
                return 0
            return (
                session.query(self.store.EmbeddingStore)
                .filter(self.store.EmbeddingStore.collection_id == collection.uuid)
                .count()
            )

    @time_it
    def add(self, chunks):
        """Insert document chunks into the store in batches, logging progress."""
        for i in range(0, len(chunks), settings.CHUNKS_BATCH_SIZE):
            batch = chunks[i : i + settings.CHUNKS_BATCH_SIZE]
            self.store.add_documents(batch)
            print(f"Inserted {i + len(batch)} / {len(chunks)} chunks")
        print("Inserted all chunks")

    def delete(self):
        """Delete the entire vector collection."""
        self.store.delete_collection()
