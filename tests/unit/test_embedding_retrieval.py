from pathlib import Path

from dongdong_bot.agent.memory import MemoryStore


def test_semantic_search_hits(tmp_path: Path):
    store = MemoryStore(str(tmp_path))
    store.save_with_embedding("買牛奶", [1.0, 0.0], date="2026-02-02")
    store.save_with_embedding("買咖啡", [0.0, 1.0], date="2026-02-02")

    results = store.semantic_search([0.9, 0.1], top_k=1, min_score=0.1)

    assert results[0][0] == "買牛奶"


def test_semantic_search_filters_noise(tmp_path: Path):
    store = MemoryStore(str(tmp_path))
    store.save_with_embedding("了什麼", [1.0, 0.0], date="2026-02-02")
    store.save_with_embedding("的事情", [0.9, 0.1], date="2026-02-02")
    store.save_with_embedding("外套顏色：淺藍", [0.8, 0.2], date="2026-02-02")

    results = store.semantic_search([0.8, 0.2], top_k=5, min_score=0.1)

    assert all(item[0] not in {"了什麼", "的事情"} for item in results)


def test_filter_by_score_keeps_top_cluster():
    results = [
        ("咖啡偏好", 0.82),
        ("外套顏色", 0.60),
        ("無關項", 0.20),
    ]

    filtered = MemoryStore.filter_by_score(results, min_score=0.3, relative_drop=0.15)

    assert ("咖啡偏好", 0.82) in filtered
    assert ("外套顏色", 0.60) not in filtered
