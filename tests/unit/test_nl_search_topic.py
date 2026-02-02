from dongdong_bot.lib.nl_search_topic import NLSearchTopicExtractor


def test_extract_search_topic():
    def fake_generate(_model: str, _prompt: str) -> str:
        return '{"is_search": true, "topic": "嘉南羊乳 公關危機", "wants_report": true}'

    extractor = NLSearchTopicExtractor(generate=fake_generate, model="gpt-4o-mini")

    plan = extractor.extract("請幫我整理嘉南羊乳公關危機")

    assert plan.is_search is True
    assert "嘉南羊乳" in plan.topic
    assert plan.wants_report is True
