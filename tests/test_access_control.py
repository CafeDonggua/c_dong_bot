from dongdong_bot.agent.allowlist_store import AllowlistEntry, AllowlistStore
from dongdong_bot.agent.skills import SkillRegistry


def test_allowlist_store(tmp_path):
    store = AllowlistStore(str(tmp_path / "allowlist.json"))
    # Empty allowlist defaults to allow
    assert store.is_allowed("user-1", "telegram") is True

    store.add(AllowlistEntry(user_id="user-1", channel_type="telegram"))
    assert store.is_allowed("user-1", "telegram") is True
    assert store.is_allowed("user-2", "telegram") is False

    store.remove("user-1", "telegram")
    # Empty again -> allow by default
    assert store.is_allowed("user-1", "telegram") is True


def test_skill_registry_toggle(tmp_path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    skill_path = skills_dir / "memory-save" / "SKILL.md"
    skill_path.parent.mkdir()
    skill_path.write_text("# 記憶保存\n", encoding="utf-8")

    registry = SkillRegistry(str(skills_dir), str(tmp_path / "skills_state.json"))
    skills = registry.list_skills()
    assert skills[0].enabled is True

    registry.set_enabled("memory-save", False)
    assert registry.is_enabled("memory-save") is False
