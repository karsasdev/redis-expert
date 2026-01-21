from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    HF_TOKEN: str = "your_huggingface_token_here"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    LLM_MODEL: str = "gpt-4.1-mini"
    MD_DOCS_PATH: str = "redis-docs"
    OPENAI_API_KEY: str = "your_openai_api_key_here"

    CHUNKS_BATCH_SIZE: int = 1000
    COLLECTION_NAME: str = "redis-knowledge-base"
    CHUNK_RETRIVAL_SIZE: int = 10

    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"  # use "pgvectordb" if app runs inside docker
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "vector_db"
    
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""

    GRADIO_SERVER_NAME: str = "0.0.0.0"
    GRADIO_SERVER_PORT: int = 7860

    @property
    def POSTGRES_DB_URI(self) -> str:
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def REDIS_URL(self) -> str:
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"


settings = Settings()
