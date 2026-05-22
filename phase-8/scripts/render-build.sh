#!/usr/bin/env bash
# Native Python build on Render (if not using Dockerfile). Run from repository root.
set -euo pipefail

pip install --upgrade pip
pip install \
  -e phase-4 \
  -e phase-5 \
  -e phase-6 \
  -e phase-7 \
  -e "phase-8[index]"

export HF_HOME="${HF_HOME:-/opt/render/project/src/.cache/huggingface}"
export TRANSFORMERS_CACHE="${TRANSFORMERS_CACHE:-$HF_HOME}"
mkdir -p "$HF_HOME"

python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5')"
