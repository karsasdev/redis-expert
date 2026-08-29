"""Application bootstrap helpers: downloading Redis docs, initializing the vector DB, and launching the Gradio UI."""

import gradio as gr
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings
from app.embeddings import get_embeddings
from app.ingestion.chunker import DocumentChunker
from app.store.pg_vector import PGVectorStore
from scripts.initialize import download_redis_docs


def initialize_redis_docs():
    """Download the Redis documentation if it isn't already present."""
    download_redis_docs()


def initialize_vector_database(by_reset: bool = False):
    """Chunk and embed the Redis docs into the vector store, unless already initialized (or forced via reset)."""
    vs = PGVectorStore(embeddings=get_embeddings())
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
