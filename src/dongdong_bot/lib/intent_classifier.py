from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import hashlib
from typing import Iterable, Tuple

from dongdong_bot.lib.embedding_client import EmbeddingClient
from dongdong_bot.lib.vector_math import cosine_similarity, top_k_scored


@dataclass(frozen=True)
class IntentExample:
    intent: str
    text: str


class IntentClassifier:
    def __init__(
        self,
        client: EmbeddingClient,
        examples: Iterable[IntentExample],
        cache_path: str | None = None,
    ) -> None:
        self._client = client
        self._examples = list(examples)
        self._cache_path = Path(cache_path) if cache_path else None
        self._vectors: list[tuple[str, list[float]]] = []
        self._build_index()

    def _build_index(self) -> None:
        cached = self._load_cache()
        if cached:
            self._vectors = cached
            return
        self._vectors = []
        for example in self._examples:
            vector = self._client.embed(example.text)
            self._vectors.append((example.intent, vector))
        self._save_cache()

    def classify(self, text: str, top_k: int = 1) -> Tuple[str | None, float]:
        if not text.strip() or not self._vectors:
            return None, 0.0
        query = self._client.embed(text)
        scored: list[tuple[str, float]] = []
        for intent, vector in self._vectors:
            scored.append((intent, cosine_similarity(query, vector)))
        top = top_k_scored(scored, top_k)
        if not top:
            return None, 0.0
        return top[0][0], top[0][1]

    def _cache_key(self) -> str:
        # Cache key depends on model and examples to invalidate when they change.
        payload = {
            "model": self._client.model,
            "examples": [{"intent": ex.intent, "text": ex.text} for ex in self._examples],
        }
        blob = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()

    def _load_cache(self) -> list[tuple[str, list[float]]] | None:
        if not self._cache_path or not self._cache_path.exists():
            return None
        try:
            data = json.loads(self._cache_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        if data.get("key") != self._cache_key():
            return None
        vectors = data.get("vectors")
        if not isinstance(vectors, list):
            return None
        cleaned: list[tuple[str, list[float]]] = []
        for item in vectors:
            if not isinstance(item, dict):
                continue
            intent = item.get("intent")
            vector = item.get("vector")
            if isinstance(intent, str) and isinstance(vector, list):
                cleaned.append((intent, vector))
        return cleaned or None

    def _save_cache(self) -> None:
        if not self._cache_path:
            return
        payload = {
            "key": self._cache_key(),
            "vectors": [
                {"intent": intent, "vector": vector} for intent, vector in self._vectors
            ],
        }
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._cache_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
