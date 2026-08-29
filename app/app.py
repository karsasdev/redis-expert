"""Application entry point: wires config, docs/vector-DB bootstrap, the chatbot, and the Gradio UI together."""

from dotenv import load_dotenv

from app.chatbot.openai import ChatBot
from app.embeddings import get_embeddings
from app.init import initialize_gradio_app, initialize_redis_docs, initialize_vector_database
from app.store.pg_vector import PGVectorStore


def create_app():
    """Bootstrap docs and the vector DB, then build and launch the chatbot's Gradio app."""
    load_dotenv(override=True)
    initialize_redis_docs()
    initialize_vector_database()
    vs = PGVectorStore(embeddings=get_embeddings())
    chatbot = ChatBot(vs)
    fn = chatbot.get_chat_function()
    initialize_gradio_app(fn)


