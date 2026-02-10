from pathlib import Path


REQUIRED_HEADINGS = [
    "## Summary",
    "## Triggers",
    "## Inputs",
    "## Outputs",
    "## Steps",
    "## Constraints",
    "## Safety",
    "## Examples",
]


def _parse_frontmatter(lines: list[str]) -> dict[str, str]:
    if not lines or lines[0].strip() != "---":
        return {}
    data: dict[str, str] = {}
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if ":" in stripped:
            key, value = stripped.split(":", 1)
            data[key.strip()] = value.strip()
    return data


def test_all_skills_have_required_structure():
    skills_dir = Path("resources/skills")
    skill_paths = sorted(skills_dir.glob("*/SKILL.md"))
    assert skill_paths, "resources/skills/ 內未找到任何 SKILL.md"

    names: set[str] = set()
    for skill_path in skill_paths:
        content = skill_path.read_text(encoding="utf-8")
        lines = content.splitlines()

        frontmatter = _parse_frontmatter(lines)
        assert frontmatter, f"{skill_path} 缺少 YAML frontmatter"
        assert frontmatter.get("name"), f"{skill_path} 缺少 name"
        assert frontmatter.get("description"), f"{skill_path} 缺少 description"
        assert frontmatter.get("version"), f"{skill_path} 缺少 version"

        name = frontmatter["name"]
        assert name not in names, f"技能名稱重複: {name}"
        names.add(name)

        for heading in REQUIRED_HEADINGS:
            assert heading in content, f"{skill_path} 缺少 {heading}"
