from datetime import datetime

from dongdong_bot.agent.memory import MemoryStore


def test_memory_recall_returns_saved_entries(tmp_path):
    store = MemoryStore(str(tmp_path))
    store.save("今天要買牛奶", date="2026-02-05")
    store.save("明天要運動", date="2026-02-05")

    results = store.query("牛奶", date="2026-02-05")
    assert "今天要買牛奶" in results[0]

    empty = store.query("咖啡", date="2026-02-05")
    assert empty == []
