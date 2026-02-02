from dongdong_bot.lib.search_schema import SearchResponse
from dongdong_bot.main import _handle_summary_command
from dongdong_bot.lib.search_formatter import SearchFormatter


class FakeSearchClient:
    def summarize_link(self, url: str) -> SearchResponse:
        return SearchResponse(
            summary=f"摘要:{url}",
            bullets=["重點"],
            sources=[url],
        )


def test_link_summary_flow():
    response = _handle_summary_command("/summary https://example.com", FakeSearchClient(), SearchFormatter())

    assert "摘要" in response
    assert "https://example.com" in response
