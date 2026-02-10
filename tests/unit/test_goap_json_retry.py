from dongdong_bot.agent.loop import GoapEngine


class FakeClient:
    def __init__(self, responses):
        self._responses = list(responses)

    def generate(self, model: str, prompt: str) -> str:
        return self._responses.pop(0)


def test_goap_json_retry():
    responses = [
        "not json",
        '{"goal":"G","action":"A","observation":"O","reply":"OK","progress":true}',
    ]
    engine = GoapEngine(
        FakeClient(responses),
        model="gpt-5-mini",
        fast_model="gpt-4o-mini",
        shortcuts_enabled=False,
        base_max_iters=1,
        max_iters_cap=1,
    )
    response = engine.respond("請記住這件事")

    assert response.reply == "OK"
