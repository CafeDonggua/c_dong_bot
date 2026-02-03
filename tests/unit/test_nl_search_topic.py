from dongdong_bot.lib.nl_search_topic import NLSearchTopicExtractor


def test_extract_search_topic():
    def fake_generate(_model: str, _prompt: str) -> str:
        return '{"is_search": true, "topic": "嘉南羊乳 公關危機", "wants_report": true}'

    extractor = NLSearchTopicExtractor(generate=fake_generate, model="gpt-4o-mini")

    plan = extractor.extract("請幫我整理嘉南羊乳公關危機")

    assert plan.is_search is True
    assert "嘉南羊乳" in plan.topic
    assert plan.wants_report is True


def test_extract_search_topic_from_codeblock():
    def fake_generate(_model: str, _prompt: str) -> str:
        return "```json\n{\"is_search\": true, \"topic\": \"測試主題\", \"wants_report\": false}\n```"

    extractor = NLSearchTopicExtractor(generate=fake_generate, model="gpt-4o-mini")

    plan = extractor.extract("請幫我整理測試主題")

    assert plan.is_search is True
    assert plan.topic == "測試主題"
    assert plan.wants_report is False


def test_extract_search_topic_from_wrapped_text():
    def fake_generate(_model: str, _prompt: str) -> str:
        return "結果如下：{\"is_search\": true, \"topic\": \"台灣能源政策\", \"wants_report\": false}"

    extractor = NLSearchTopicExtractor(generate=fake_generate, model="gpt-4o-mini")

    plan = extractor.extract("查一下台灣能源政策")

    assert plan.is_search is True
    assert plan.topic == "台灣能源政策"


def test_extract_search_topic_retry_on_invalid_json():
    calls = {"count": 0}

    def fake_generate(_model: str, _prompt: str) -> str:
        calls["count"] += 1
        if calls["count"] == 1:
            return "這不是 JSON"
        return "{\"is_search\": true, \"topic\": \"新聞摘要\", \"wants_report\": true}"

    extractor = NLSearchTopicExtractor(generate=fake_generate, model="gpt-4o-mini")

    plan = extractor.extract("幫我整理新聞摘要")

    assert plan.is_search is True
    assert plan.topic == "新聞摘要"
    assert plan.wants_report is True
    assert calls["count"] == 2


def test_extract_search_topic_with_url():
    def fake_generate(_model: str, _prompt: str) -> str:
        return '{"is_search": false, "topic": "", "wants_report": false}'

    extractor = NLSearchTopicExtractor(generate=fake_generate, model="gpt-4o-mini")

    plan = extractor.extract("請幫我整理 https://example.com")

    assert plan.is_search is True
    assert plan.url == "https://example.com"


def test_extract_search_topic_save_intent_override():
    def fake_generate(_model: str, _prompt: str) -> str:
        return '{"is_search": true, "topic": "測試主題", "wants_report": false}'

    extractor = NLSearchTopicExtractor(generate=fake_generate, model="gpt-4o-mini")

    plan = extractor.extract("幫我整理測試主題並儲存")

    assert plan.wants_report is True
