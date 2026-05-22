# Mutual Fund FAQ API — production image for Render (frontend on Vercel).
FROM python:3.11-slim-bookworm

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# RAG stack: configs + corpus index (paths are repo-relative in each phase package).
COPY phase-1/config ./phase-1/config
COPY phase-3/data ./phase-3/data
COPY phase-4 ./phase-4
COPY phase-5 ./phase-5
COPY phase-6 ./phase-6
COPY phase-7 ./phase-7
COPY phase-8 ./phase-8

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
        -e ./phase-4 \
        -e ./phase-5 \
        -e ./phase-6 \
        -e ./phase-7 \
        -e "./phase-8[index]"

ENV HF_HOME=/app/.cache/huggingface \
    TRANSFORMERS_CACHE=/app/.cache/huggingface \
  PORT=8000

# Warm embedding model at build time (smaller cold start on Render).
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5')"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz')" || exit 1

CMD ["sh", "-c", "mf-api serve --host 0.0.0.0 --port ${PORT:-8000}"]
