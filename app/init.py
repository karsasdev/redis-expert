from langchain_text_splitters import RecursiveCharacterTextSplitter
from pygments.styles import vs
import gradio as gr

from app.config import settings
from app.ingestion.chunker import DocumentChunker
from app.utils import get_project_root
from scripts.initialize import download_redis_docs
from app.embeddings import get_embeddings
from app.store.pg_vector import PGVectorStore

VECTOR_INIT_MARKER = ".vector_db_initialized"

def initialize_redis_docs():
    download_redis_docs()


def initialize_vector_database(by_reset: bool = False):

    vdb_init_file = ".vector_db_initialized"
    out_dir = get_project_root()  # choose a stable output folder
    marker_file = out_dir / vdb_init_file
    if marker_file.exists() and not by_reset:
        print("Vector DB already initialized. Skipping.")
        return
    vs = PGVectorStore(embeddings=get_embeddings())
    if by_reset:
        print("Deleting existing vectorstore...")
        vs.delete()

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunker = DocumentChunker(splitter=splitter)
    chunks = chunker.doc_to_chunks()
    vs = PGVectorStore(embeddings=get_embeddings())
    vs.add(chunks)
    print(f"Vector database initialization complete - chunks added: {len(chunks)}")
    marker_file.write_text("ok")

def initialize_gradio_app(chat_func, title: str = "Chat with RedisAI", inbrowser: bool = True):
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
