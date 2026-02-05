from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List
import json


@dataclass(frozen=True)
class SkillInfo:
    name: str
    description: str
    enabled: bool


class SkillRegistry:
    def __init__(self, skills_dir: str, state_path: str) -> None:
        self.skills_dir = Path(skills_dir)
        self.state_path = Path(state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

    def list_skills(self) -> List[SkillInfo]:
        states = self._load_state()
        skills = []
        for skill_name in self._discover_skill_names():
            description = self._load_description(skill_name)
            enabled = bool(states.get(skill_name, True))
            skills.append(SkillInfo(skill_name, description, enabled))
        return skills

    def is_enabled(self, skill_name: str) -> bool:
        states = self._load_state()
        return bool(states.get(skill_name, True))

    def set_enabled(self, skill_name: str, enabled: bool) -> None:
        states = self._load_state()
        states[skill_name] = bool(enabled)
        self._write_state(states)

    def seed_states(self, skills: Iterable[SkillInfo]) -> None:
        states = {skill.name: skill.enabled for skill in skills}
        self._write_state(states)

    def _discover_skill_names(self) -> List[str]:
        if not self.skills_dir.exists():
            return []
        names = []
        for entry in self.skills_dir.iterdir():
            if entry.is_dir() and (entry / "SKILL.md").exists():
                names.append(entry.name)
        return sorted(names)

    def _load_description(self, skill_name: str) -> str:
        skill_path = self.skills_dir / skill_name / "SKILL.md"
        if not skill_path.exists():
            return ""
        for line in skill_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("# "):
                return stripped[2:].strip()
        return ""

    def _load_state(self) -> Dict[str, bool]:
        if not self.state_path.exists():
            return {}
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        if not isinstance(data, dict):
            return {}
        return {str(key): bool(value) for key, value in data.items()}

    def _write_state(self, data: Dict[str, bool]) -> None:
        tmp_path = self.state_path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(self.state_path)
