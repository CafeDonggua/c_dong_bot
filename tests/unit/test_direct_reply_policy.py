from dongdong_bot.agent.loop import GoapEngine
from dongdong_bot.lib.response_style import ResponseStyler


class FakeClient:
    def __init__(self, response: str) -> None:
        self._response = response

    def generate(self, model: str, prompt: str) -> str:
        return self._response


def test_direct_reply_short_circuit():
    engine = GoapEngine(
        FakeClient("OK"),
        model="gpt-5-mini",
        fast_model="gpt-4o-mini",
    )

    response = engine.respond("你好嗎")

    assert response.reply == "OK"
    assert response.decision == "direct_reply"


def test_response_style_adds_follow_up():
    styler = ResponseStyler()
    styled = styler.style("我可以協助你整理資訊。", "幫我整理一下")

    assert "你希望我優先處理哪一塊" in styled.reply


def test_response_style_adds_tips_for_ambiguous():
    styler = ResponseStyler()
    styled = styler.style("我可以幫你。", "你可以做什麼")

    assert "你可以試試" in styled.reply
