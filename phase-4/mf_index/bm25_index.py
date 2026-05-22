"""BM25 lexical index (architecture §4.3, edge 4.14)."""

from __future__ import annotations

import json
import pickle
import re
from pathlib import Path

from rank_bm25 import BM25Okapi

from mf_index.models import ChunkRecord
from mf_index.paths import BM25_DIR, BM25_STOPWORDS

_TOKEN = re.compile(r"[a-z0-9%₹]+", re.I)


def load_stopwords(path: Path = BM25_STOPWORDS) -> frozenset[str]:
    if not path.is_file():
        return frozenset()
    words = {
        line.strip().lower()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }
    return frozenset(words)


def tokenize(text: str, stopwords: frozenset[str]) -> list[str]:
    raw = _TOKEN.findall(text.lower())
    return [t for t in raw if t not in stopwords and len(t) > 1]


class BM25Index:
    def __init__(
        self,
        *,
        chunk_ids: list[str],
        bm25: BM25Okapi,
        corpus_tokens: list[list[str]],
        stopwords: frozenset[str],
    ) -> None:
        self.chunk_ids = chunk_ids
        self._bm25 = bm25
        self._corpus_tokens = corpus_tokens
        self._stopwords = stopwords
        self._id_to_idx = {cid: i for i, cid in enumerate(chunk_ids)}

    @classmethod
    def build(cls, chunks: list[ChunkRecord], stopwords: frozenset[str] | None = None) -> BM25Index:
        sw = stopwords if stopwords is not None else load_stopwords()
        ids = [c.chunk_id for c in chunks]
        corpus_tokens = [tokenize(c.text, sw) for c in chunks]
        # BM25 needs non-empty token lists
        safe = [t if t else ["_"] for t in corpus_tokens]
        bm25 = BM25Okapi(safe)
        return cls(chunk_ids=ids, bm25=bm25, corpus_tokens=corpus_tokens, stopwords=sw)

    def scores(self, query: str, *, allowed_indices: list[int] | None = None) -> list[float]:
        q_tokens = tokenize(query, self._stopwords)
        if not q_tokens:
            return [0.0] * len(self.chunk_ids)
        raw = self._bm25.get_scores(q_tokens)
        if allowed_indices is None:
            return [float(x) for x in raw]
        out = [0.0] * len(self.chunk_ids)
        for idx in allowed_indices:
            out[idx] = float(raw[idx])
        return out

    def save(self, directory: Path = BM25_DIR) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        payload = {
            "chunk_ids": self.chunk_ids,
            "corpus_tokens": self._corpus_tokens,
            "stopwords": sorted(self._stopwords),
        }
        tmp = directory / "bm25.pkl.tmp"
        final = directory / "bm25.pkl"
        meta_tmp = directory / "meta.json.tmp"
        meta_final = directory / "meta.json"
        with tmp.open("wb") as f:
            pickle.dump(self._bm25, f)
        meta_tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp.replace(final)
        meta_tmp.replace(meta_final)

    @classmethod
    def load(cls, directory: Path = BM25_DIR) -> BM25Index:
        pkl = directory / "bm25.pkl"
        meta_path = directory / "meta.json"
        if not pkl.is_file() or not meta_path.is_file():
            raise FileNotFoundError(f"BM25 index missing under {directory}")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        with pkl.open("rb") as f:
            bm25 = pickle.load(f)
        return cls(
            chunk_ids=list(meta["chunk_ids"]),
            bm25=bm25,
            corpus_tokens=list(meta["corpus_tokens"]),
            stopwords=frozenset(meta["stopwords"]),
        )
