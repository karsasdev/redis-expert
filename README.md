# Redis Expert — RAG-based Redis Assistant

Redis Expert is an AI-powered assistant that answers Redis questions by retrieving context directly from official Redis documentation using Retrieval-Augmented Generation (RAG).

## Architecture
```
User Query
    │
    ▼
Gradio Chat UI
    │
    ▼
HuggingFace Embeddings → PGVector Semantic Search
    │
    ▼
Top-K Relevant Redis Doc Chunks
    │
    ▼
LangChain + OpenAI GPT-4o-mini → Answer
```

- Redis docs are auto-downloaded and chunked on first run
- Chunks are embedded and stored in PostgreSQL (PGVector)
- Each query is embedded and matched semantically — no keyword search
- LangChain orchestrates retrieval + generation

## Features

- Auto-downloads and processes Redis documentation from GitHub
- Semantic search using HuggingFace embeddings + PGVector
- Interactive Gradio chat interface
- Powered by LangChain and OpenAI GPT-4o-mini

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | OpenAI GPT-4o-mini |
| Embeddings | HuggingFace all-MiniLM-L6-v2 |
| Vector DB | PostgreSQL + PGVector |
| Orchestration | LangChain |
| UI | Gradio |
| Package Manager | uv |
| Containerization | Docker + Docker Compose |

## Quick Start

### Prerequisites
- Docker and Docker Compose
- OpenAI API Key
- HuggingFace Token

### Run with Docker
```bash
git clone https://github.com/karsasdev/redis-expert.git
cd redis-expert
cp .env-docker .env        # Add your OPENAI_API_KEY and HF_TOKEN
docker-compose up -d
open http://localhost:7860
```

The app auto-downloads Redis docs and initializes the vector DB on first run.

### Local Development
```bash
pip install uv
uv sync
cp .env-local .env         # Add your credentials
uv run python main.py
```

## Example Questions

- "How do I set up Redis persistence?"
- "What are Redis streams and how do they differ from Kafka?"
- "Explain Redis pub/sub patterns"
- "How does single-threaded execution work in Redis?"
- "Show me Lua scripting in Redis"

See [sample-chat.md](./sample-chat.md) for full example conversations.

## Attribution
This project uses Redis documentation © Redis Ltd., licensed under CC BY-NC-SA 4.0 / CC BY-SA 4.0 (see [LICENSE](https://github.com/redis/docs/blob/main/LICENSE)).
