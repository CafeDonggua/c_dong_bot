from pathlib import Path

from dongdong_bot.agent.memory import MemoryStore


def test_memory_store_save(tmp_path: Path):
    store = MemoryStore(str(tmp_path))
    path = store.save("記住買牛奶", date="2026-02-02")

    assert path.exists()
    assert path.parent.name == "memory"
    content = path.read_text(encoding="utf-8")
    assert "記住買牛奶" in content


def test_memory_store_query_range(tmp_path: Path):
    store = MemoryStore(str(tmp_path))
    store.save("記住牛奶", date="2026-02-01")
    store.save("記住咖啡", date="2026-02-02")

    results = store.query_range("記住", start="2026-02-01", end="2026-02-02")

    assert len(results) == 2


def test_memory_store_summarize_results(tmp_path: Path):
    store = MemoryStore(str(tmp_path))
    results = [
        "這是一段很長的內容" * 10,
        "這是一段很長的內容" * 10,
        "短內容",
    ]

    summarized = store.summarize_results(results, max_items=2, max_chars=20)

    assert len(summarized) == 2
    assert summarized[0].endswith("…")
    assert summarized[1] == "短內容"
