from dotenv import load_dotenv

from app.chatbot.openai import ChatBot
from app.embeddings import get_embeddings
from app.init import initialize_redis_docs, initialize_vector_database, initialize_gradio_app
from app.store.pg_vector import PGVectorStore


def create_app():
    load_dotenv(override=True)
    initialize_redis_docs()
    initialize_vector_database()
    vs = PGVectorStore(embeddings=get_embeddings())
    chatbot = ChatBot(vs)
    fn = chatbot.get_chat_function()
    initialize_gradio_app(fn)


