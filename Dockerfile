FROM python:3.14-slim

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl

# install uv
RUN pip install --no-cache-dir uv

# copy only dependency files first (for caching)
COPY pyproject.toml uv.lock /workspace/

RUN uv sync --frozen --no-dev

# copy only required source files into /workspace/src
COPY main.py /workspace/src/main.py
COPY app /workspace/src/app
COPY scripts /workspace/src/scripts

EXPOSE 7860
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace/src

CMD ["uv", "run", "python", "main.py"]
