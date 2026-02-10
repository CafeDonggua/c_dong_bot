from types import SimpleNamespace

from dongdong_bot.main import _resolve_memory_content


class FakeClient:
    def generate(self, model: str, prompt: str) -> str:
        return "後天下午要剪頭髮"


def test_resolve_memory_content_uses_response_content():
    response = SimpleNamespace(decision="memory_save", memory_content="記住牛奶")
    content, normalized = _resolve_memory_content(
        "使用者輸入", response, FakeClient(), "gpt-4o-mini", True
    )
    assert content == "記住牛奶"
    assert normalized is False


def test_resolve_memory_content_falls_back_to_user_text():
    response = SimpleNamespace(decision="memory_save", memory_content=None)
    content, normalized = _resolve_memory_content(
        "我有一包咖啡豆", response, FakeClient(), "gpt-4o-mini", True
    )
    assert content == "後天下午要剪頭髮"
    assert normalized is True


def test_resolve_memory_content_ignores_non_memory_save():
    response = SimpleNamespace(decision="direct_reply", memory_content=None)
    content, normalized = _resolve_memory_content(
        "你好", response, FakeClient(), "gpt-4o-mini", True
    )
    assert content is None
    assert normalized is False


def test_resolve_memory_content_requires_explicit_save():
    response = SimpleNamespace(decision="memory_save", memory_content="記住牛奶")
    content, normalized = _resolve_memory_content(
        "你好", response, FakeClient(), "gpt-4o-mini", False
    )
    assert content is None
    assert normalized is False
