"""Entry point script: builds and launches the Redis expert chatbot app."""

from app.app import create_app

if __name__ == "__main__":
    create_app()
