# Redis Expert: RAG-based Redis Assistant

**Redis Expert** is a powerful, AI-driven assistant designed to help developers and Redis enthusiasts navigate and understand Redis documentation with ease. It leverages Retrieval-Augmented Generation (RAG) to provide accurate, context-aware answers to complex questions about Redis.

## Features

- Auto-downloads and processes Redis documentation from GitHub
- Semantic search using embeddings and PGVector
- Interactive Gradio chat interface
- Powered by LangChain and OpenAI

## Tech Stack

- **Framework**: LangChain
- **LLM**: OpenAI GPT-4o-mini
- **Embeddings**: HuggingFace (configurable, default: `all-MiniLM-L6-v2`)
- **Vector DB**: PostgreSQL with PGVector
- **UI**: Gradio
- **Package Manager**: uv

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API Key
- HuggingFace Token

### Setup

1. **Clone and configure**:
   ```bash
   git clone https://github.com/your-username/redis-expert.git
   cd redis-expert
   cp .env-docker .env
   # Edit .env with your OPENAI_API_KEY and HF_TOKEN
   ```

2. **Run with Docker**:
   ```bash
   docker-compose up -d
   ```

3. **Access the app**: Open `http://localhost:7860`

The app automatically downloads Redis docs and initializes the vector database on first run.

## Local Development

```bash
pip install uv
uv sync
cp .env-local .env
# Edit .env with your credentials
uv run python main.py
```

## Usage

Ask Redis-related questions in the chat interface. The system uses semantic search to find relevant documentation and generates answers using OpenAI.

Example questions:
- "How do I set up Redis persistence?"
- "What are Redis streams?"
- "Explain Redis pub/sub patterns"

See [sample-chat.md](sample-chat.md) for example conversations (single-threaded execution, Redis vs Kafka streams, Lua scripting, and more).

## Attribution

This project uses Redis documentation © Redis Ltd., licensed under CC BY-NC-SA 4.0 / CC BY-SA 4.0 (see https://github.com/redis/docs/blob/main/LICENSE).

