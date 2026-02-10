from dongdong_bot.agent.loop import GoapEngine, StepResult


class FakeClient:
    def __init__(self, responses):
        self._responses = list(responses)

    def generate(self, model: str, prompt: str) -> str:
        return self._responses.pop(0)


def test_goap_stops_on_repeated_observation():
    responses = [
        '{"goal":"G1","action":"A1","observation":"O1","reply":"R1","progress":false}',
        '{"goal":"G1","action":"A1","observation":"O1","reply":"R2","progress":false}',
    ]
    engine = GoapEngine(
        FakeClient(responses),
        model="gpt-5-mini",
        fast_model="gpt-4o-mini",
        shortcuts_enabled=False,
        base_max_iters=3,
    )
    response = engine.respond("請記住這件事")

    assert response.stop_reason == "loop_detected"
    assert "重複迴圈" in response.reply


def test_goap_returns_reply_on_progress():
    responses = [
        '{"goal":"G1","action":"A1","observation":"O1","reply":"R1","progress":true}',
    ]
    engine = GoapEngine(
        FakeClient(responses),
        model="gpt-5-mini",
        fast_model="gpt-4o-mini",
        shortcuts_enabled=False,
        base_max_iters=1,
        max_iters_cap=1,
        no_progress_limit=1,
    )
    response = engine.respond("請記住這件事")

    assert response.stop_reason is None
    assert response.reply == "R1"


def test_goap_prompt_compaction():
    engine = GoapEngine(
        FakeClient(["{\"goal\":\"G\",\"action\":\"A\",\"observation\":\"O\",\"reply\":\"R\",\"progress\":true}"]),
        model="gpt-5-mini",
        fast_model="gpt-4o-mini",
        shortcuts_enabled=False,
        base_max_iters=1,
    )
    history = [
        StepResult("G1", "A1", "O1", "R1", True),
        StepResult("G2", "A2", "O2", "R2", True),
        StepResult("G3", "A3", "O3", "R3", True),
        StepResult("G4", "A4", "O4", "R4", True),
        StepResult("G5", "A5", "O5", "R5", True),
    ]

    prompt = engine._build_prompt("測試", history)

    assert "前序摘要" in prompt
