"""Factory for the HuggingFace embedding model used to embed and retrieve document chunks."""

from langchain_huggingface import HuggingFaceEmbeddings

from app.config import settings


def get_embeddings():
    """Create a HuggingFace embeddings instance using the configured embedding model."""
    return HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)

