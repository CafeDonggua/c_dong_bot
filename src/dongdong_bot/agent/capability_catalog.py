from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class Capability:
    name: str
    description: str
    required_inputs: list[str]
    example_requests: list[str]
    clarifications: dict[str, str]


class CapabilityCatalog:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._capabilities: dict[str, Capability] = {}
        self._load()

    def _load(self) -> None:
        raw = self.path.read_text(encoding="utf-8")
        data = json.loads(raw)
        if isinstance(data, dict) and "capabilities" in data:
            items = data["capabilities"]
        else:
            items = data
        if not isinstance(items, list):
            raise ValueError("capabilities 應為 list")
        for item in items:
            capability = self._parse_capability(item)
            if capability.name in self._capabilities:
                raise ValueError(f"capability 名稱重複: {capability.name}")
            self._capabilities[capability.name] = capability

    def _parse_capability(self, item: Any) -> Capability:
        if not isinstance(item, dict):
            raise ValueError("capability 項目格式錯誤")
        name = str(item.get("name", "")).strip()
        description = str(item.get("description", "")).strip()
        required_inputs = item.get("required_inputs", [])
        example_requests = item.get("example_requests", [])
        clarifications = item.get("clarifications", {})
        if not name or not description:
            raise ValueError("capability 必須包含 name 與 description")
        if not isinstance(required_inputs, list):
            raise ValueError(f"{name} required_inputs 必須是 list")
        if not isinstance(example_requests, list):
            raise ValueError(f"{name} example_requests 必須是 list")
        if not isinstance(clarifications, dict):
            raise ValueError(f"{name} clarifications 必須是 dict")
        return Capability(
            name=name,
            description=description,
            required_inputs=[str(x) for x in required_inputs],
            example_requests=[str(x) for x in example_requests],
            clarifications={str(k): str(v) for k, v in clarifications.items()},
        )

    def list_capabilities(self) -> list[Capability]:
        return list(self._capabilities.values())

    def get(self, name: str) -> Capability | None:
        return self._capabilities.get(name)

    def capability_names(self) -> list[str]:
        return list(self._capabilities.keys())

    def to_prompt_block(self) -> str:
        lines: list[str] = []
        for capability in self.list_capabilities():
            lines.append(f"- 名稱: {capability.name}")
            lines.append(f"  描述: {capability.description}")
            if capability.required_inputs:
                lines.append(
                    "  必要輸入: " + ", ".join(capability.required_inputs)
                )
            if capability.example_requests:
                examples = " | ".join(capability.example_requests)
                lines.append(f"  範例: {examples}")
        return "\n".join(lines)


def load_capability_catalog(path: str | Path) -> CapabilityCatalog:
    return CapabilityCatalog(path)
