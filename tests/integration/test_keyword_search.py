from dongdong_bot.lib.search_schema import SearchResponse
from dongdong_bot.main import _handle_search_command
from dongdong_bot.lib.search_formatter import SearchFormatter


class FakeSearchClient:
    def search_keyword(self, query: str) -> SearchResponse:
        return SearchResponse(
            summary=f"摘要:{query}",
            bullets=["重點"],
            sources=["https://example.com"],
        )


def test_keyword_search_flow():
    response = _handle_search_command("/search 測試關鍵字", FakeSearchClient(), SearchFormatter())

    assert "摘要" in response
    assert "來源" in response
