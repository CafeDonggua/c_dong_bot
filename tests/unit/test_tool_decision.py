from dongdong_bot.agent.loop import GoapEngine


class FakeClient:
    def __init__(self, response: str) -> None:
        self._response = response

    def generate(self, model: str, prompt: str) -> str:
        return self._response


def test_tool_decision_use_tool():
    response_json = (
        '{"goal":"G","action":"A","observation":"O","reply":"R","progress":true}'
    )
    def fake_intent_classifier(_text: str):
        return "use_tool", 0.99
    engine = GoapEngine(
        FakeClient(response_json),
        model="gpt-5-mini",
        fast_model="gpt-4o-mini",
        intent_classifier=fake_intent_classifier,
        base_max_iters=1,
    )

    response = engine.respond("今天台北天氣如何")

    assert response.decision == "use_tool"
