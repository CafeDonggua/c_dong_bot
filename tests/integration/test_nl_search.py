from dongdong_bot.lib.search_schema import SearchResponse
from dongdong_bot.lib.search_formatter import SearchFormatter
from dongdong_bot.lib.nl_search_topic import NLSearchTopicExtractor


def handle_nl_search(text: str, extractor, search_client, formatter):
    plan = extractor.extract(text)
    if not plan.is_search or not plan.topic:
        return ""
    response = search_client.search_keyword(plan.topic)
    return formatter.format(response)


class FakeSearchClient:
    def search_keyword(self, query: str) -> SearchResponse:
        return SearchResponse(
            summary=f"摘要:{query}",
            bullets=["重點"],
            sources=["https://example.com"],
        )


def test_nl_search_flow():
    def fake_generate(_model: str, _prompt: str) -> str:
        return '{"is_search": true, "topic": "測試主題", "wants_report": false}'

    extractor = NLSearchTopicExtractor(generate=fake_generate, model="gpt-4o-mini")
    response = handle_nl_search(
        "請幫我整理測試主題",
        extractor,
        FakeSearchClient(),
        SearchFormatter(),
    )

    assert "摘要" in response
    assert "來源" in response
