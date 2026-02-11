from pathlib import Path

from dongdong_bot.agent.memory import MemoryStore
from dongdong_bot.main import _memory_query_hint


class FakeEmbeddingClient:
    def embed(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]


def test_memory_query_hint_detects_sport_preference_question(tmp_path: Path):
    store = MemoryStore(str(tmp_path))
    hinted, source, hits = _memory_query_hint(
        "我喜歡什麼運動？",
        None,
        FakeEmbeddingClient(),
        store,
    )
    assert hinted is True
    assert source in {"keyword", "recent_empty", "no_match", "embedding_index", "recent_semantic"}
    assert hits >= 0
