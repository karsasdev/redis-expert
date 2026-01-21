
from langchain_postgres import PGVector

from app.config import settings
from app.utils.decorators import time_it


class PGVectorStore:
    def __init__(self, embeddings):
        self.store = PGVector(
            connection=settings.POSTGRES_DB_URI,
            embeddings=embeddings,
            collection_name=settings.COLLECTION_NAME,
            use_jsonb=True,
        )

    def get(self, query: str):
        return self.store.similarity_search(query, k=settings.CHUNK_RETRIVAL_SIZE)

    @time_it
    def add(self, chunks):
        for i in range(0, len(chunks), settings.CHUNKS_BATCH_SIZE):
            batch = chunks[i : i + settings.CHUNKS_BATCH_SIZE]
            self.store.add_documents(batch)
            print(f"Inserted {i + len(batch)} / {len(chunks)} chunks")
        print("Inserted all chunks")

    def delete(self):
        self.store.delete_collection()
