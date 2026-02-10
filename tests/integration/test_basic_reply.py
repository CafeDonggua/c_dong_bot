from dongdong_bot.agent.loop import GoapEngine
from dongdong_bot.lib.response_style import ResponseStyler


class FakeClient:
    def generate(self, model: str, prompt: str) -> str:
        return '{"goal":"G","action":"A","observation":"O","reply":"你好，我是 DongDong。","progress":true}'


def test_basic_reply_flow():
    engine = GoapEngine(
        FakeClient(),
        model="gpt-5-mini",
        fast_model="gpt-4o-mini",
        base_max_iters=1,
    )
    response = engine.respond("你好")

    assert response.stop_reason is None
    assert "DongDong" in response.reply


def test_basic_reply_style_flow():
    styler = ResponseStyler()
    styled = styler.style("我可以幫你處理。", "你可以做什麼")

    assert "你可以試試" in styled.reply
