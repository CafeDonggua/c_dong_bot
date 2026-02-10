from __future__ import annotations

import json
from pathlib import Path

from dongdong_bot.agent.capability_catalog import CapabilityCatalog
from dongdong_bot.agent.intent_router import IntentRouter


class FakeClient:
    def __init__(self, response: str) -> None:
        self._response = response

    def generate(self, model: str, prompt: str) -> str:
        return self._response


def _make_catalog(tmp_path: Path) -> CapabilityCatalog:
    path = tmp_path / "caps.yaml"
    payload = {
        "capabilities": [
            {
                "name": "memory_save",
                "description": "保存記憶",
                "required_inputs": ["content"],
                "example_requests": ["我喜歡咖啡"],
                "clarifications": {"content": "要我記住什麼？"},
            },
            {
                "name": "direct_reply",
                "description": "一般對話",
                "required_inputs": [],
                "example_requests": ["你好"],
                "clarifications": {},
            },
        ]
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return CapabilityCatalog(path)


def test_route_parses_decision(tmp_path: Path) -> None:
    catalog = _make_catalog(tmp_path)
    client = FakeClient(
        '{"capability":"memory_save","missing_inputs":[],"needs_clarification":false,"confidence":0.9}'
    )
    router = IntentRouter(client.generate, "gpt-4o-mini", catalog)

    decision = router.route("我喜歡咖啡")

    assert decision.capability == "memory_save"
    assert decision.needs_clarification is False
    assert decision.missing_inputs == []


def test_route_builds_clarification(tmp_path: Path) -> None:
    catalog = _make_catalog(tmp_path)
    client = FakeClient(
        '{"capability":"memory_save","missing_inputs":["content"],"needs_clarification":true,"confidence":0.4}'
    )
    router = IntentRouter(client.generate, "gpt-4o-mini", catalog)

    decision = router.route("記住一下")
    question = router.build_clarification_question(decision)

    assert question == "要我記住什麼？"


def test_route_handles_invalid_capability(tmp_path: Path) -> None:
    catalog = _make_catalog(tmp_path)
    client = FakeClient(
        '{"capability":"unknown","missing_inputs":[],"needs_clarification":false,"confidence":0.1}'
    )
    router = IntentRouter(client.generate, "gpt-4o-mini", catalog)

    decision = router.route("你好")

    assert decision.capability == "direct_reply"
    assert decision.needs_clarification is True
