from dongdong_bot.agent.loop import GoapEngine


class FakeClient:
    def generate(self, model: str, prompt: str) -> str:
        return (
            '{"goal":"回憶","action":"查詢","observation":"完成",'
            '"reply":"我正在幫你查。","progress":true,'
            '"memory_query":"牛奶","memory_date":"2026-02-02"}'
        )


def test_goap_memory_query_fields():
    engine = GoapEngine(
        FakeClient(),
        model="gpt-5-mini",
        fast_model="gpt-4o-mini",
        shortcuts_enabled=False,
        base_max_iters=1,
    )
    response = engine.respond("請回憶今天的記憶")

    assert response.memory_query == "牛奶"
    assert response.memory_date == "2026-02-02"


def test_memory_query_threshold_override():
    def classify(_: str):
        return "memory_query", 0.66

    engine = GoapEngine(
        FakeClient(),
        model="gpt-5-mini",
        fast_model="gpt-4o-mini",
        intent_classifier=classify,
    )
    response = engine.respond("我有什麼咖啡豆？")

    assert response.decision == "memory_query"


def test_memory_query_below_threshold_falls_back():
    def classify(_: str):
        return "memory_query", 0.64

    engine = GoapEngine(
        FakeClient(),
        model="gpt-5-mini",
        fast_model="gpt-4o-mini",
        intent_classifier=classify,
    )
    response = engine.respond("我有什麼咖啡豆？")

    assert response.decision == "direct_reply"
