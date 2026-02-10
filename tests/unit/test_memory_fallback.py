from __future__ import annotations

import json
from pathlib import Path

from dongdong_bot.main import _semantic_memory_fallback
from dongdong_bot.agent.memory import MemoryStore


class FakeEmbeddingClient:
    def __init__(self, vector: list[float]) -> None:
        self._vector = vector

    def embed(self, text: str) -> list[float]:
        return list(self._vector)


def test_semantic_memory_fallback_hits(tmp_path: Path) -> None:
    store = MemoryStore(str(tmp_path))
    record = {
        "id": "abc",
        "date": "2026-02-02",
        "content": "後天中午12點剪頭",
        "vector": [0.1, 0.2, 0.3],
        "created_at": "2026-02-02T12:00:00",
    }
    store.embedding_index_path.write_text(
        json.dumps(record, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    embedding_client = FakeEmbeddingClient([0.1, 0.2, 0.3])
    results, source = _semantic_memory_fallback(
        "我最近有什麼行程？", embedding_client, store, min_score=0.2
    )

    assert "後天中午12點剪頭" in results
    assert source == "embedding_index"


def test_fallback_uses_recent_entries_when_index_missing(tmp_path: Path) -> None:
    store = MemoryStore(str(tmp_path))
    today = "2026-02-04"
    memory_path = store.memory_dir / f"{today}.md"
    memory_path.write_text("- 後天下午要剪頭髮\n", encoding="utf-8")

    embedding_client = FakeEmbeddingClient([0.2, 0.2, 0.2])
    results, source = _semantic_memory_fallback(
        "我最近有什麼行程？", embedding_client, store, min_score=0.1
    )

    assert "後天下午要剪頭髮" in results
    assert source == "recent_semantic"
