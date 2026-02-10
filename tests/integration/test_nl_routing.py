from __future__ import annotations

from pathlib import Path

from dongdong_bot.agent.capability_catalog import CapabilityCatalog
from dongdong_bot.agent.intent_router import IntentRouter


class FakeClient:
    def __init__(self, response: str) -> None:
        self._response = response

    def generate(self, model: str, prompt: str) -> str:
        return self._response


def test_nl_routing_uses_catalog_file() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    catalog_path = repo_root / "src" / "dongdong_bot" / "agent" / "capabilities.yaml"
    catalog = CapabilityCatalog(catalog_path)
    client = FakeClient(
        '{"capability":"memory_query","missing_inputs":[],"needs_clarification":false,"confidence":0.8}'
    )
    router = IntentRouter(client.generate, "gpt-4o-mini", catalog)

    decision = router.route("我之前說過什麼")

    assert decision.capability == "memory_query"
