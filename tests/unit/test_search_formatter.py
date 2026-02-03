from dongdong_bot.lib.search_formatter import SearchFormatter
from dongdong_bot.lib.search_schema import SearchResponse


def test_format_search_response():
    response = SearchResponse(
        summary="摘要內容",
        bullets=["重點一", "重點二"],
        sources=["https://example.com"],
    )

    text = SearchFormatter.format(response)

    assert "摘要" in text
    assert "重點" in text
    assert "來源" in text
    assert "https://example.com" in text


def test_format_search_response_with_placeholders():
    response = SearchResponse(
        summary="",
        bullets=[],
        sources=["https://example.com"],
    )

    text = SearchFormatter.format(response)

    assert "(無摘要)" in text
    assert "(無重點)" in text
    assert "https://example.com" in text


def test_format_empty_response_shows_hint():
    response = SearchResponse(
        summary="",
        bullets=[],
        sources=[],
        raw_text="",
    )

    text = SearchFormatter.format(response)

    assert "找不到相關結果" in text
