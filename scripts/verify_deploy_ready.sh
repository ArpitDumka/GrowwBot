#!/usr/bin/env bash
# Pre-push checklist. From repo root: bash scripts/verify_deploy_ready.sh [--docker]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
DOCKER=0
[[ "${1:-}" == "--docker" ]] && DOCKER=1
FAIL=0

check() {
  if [[ -e "$2" ]]; then echo "  OK  $1"
  else echo "  FAIL $1 — missing: $2"; FAIL=$((FAIL+1)); fi
}

echo ""
echo "=== Deploy readiness (Render API + Vercel UI) ==="
echo ""
echo "Deploy config:"
check "render.yaml" "$ROOT/render.yaml"
check "Dockerfile" "$ROOT/Dockerfile"
check "Vercel config" "$ROOT/phase-8/web/vercel.json"

echo ""
echo "RAG data (commit before push):"
check "chunks.jsonl" "$ROOT/phase-3/data/chunks.jsonl"
check "index manifest" "$ROOT/phase-4/data/index/index_manifest.json"
check "Chroma" "$ROOT/phase-4/data/index/chroma"
check "BM25" "$ROOT/phase-4/data/index/bm25"

cd "$ROOT/phase-8" && python -m pytest phase8_tests -q --tb=no
cd "$ROOT/phase-8/web" && npm run build

if [[ "$DOCKER" -eq 1 ]]; then
  docker build -t mf-faq-api:test "$ROOT"
fi

if [[ "$FAIL" -gt 0 ]]; then echo "NOT READY"; exit 1; fi
echo "READY for git push. See docs/DEPLOY.md"
