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

    assert "原因" in text
    assert "建議" in text
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


def test_format_error_message():
    text = SearchFormatter.format_error("搜尋模型不可用", "請確認 API KEY")

    assert "搜尋失敗" in text
    assert "搜尋模型不可用" in text
    assert "請確認 API KEY" in text
