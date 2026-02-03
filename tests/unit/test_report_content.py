from dongdong_bot.lib.report_content import normalize_report_content
from tests.helpers.search_fixtures import make_search_response


def test_normalize_report_content_fills_missing_sections():
    response = make_search_response()

    content = normalize_report_content(
        response,
        reason="找不到相關結果",
        suggestion="請改用其他關鍵字",
    )

    assert "原因" in content.summary
    assert any("建議" in item for item in content.bullets)
    assert content.sources


def test_normalize_report_content_uses_raw_text_when_summary_missing():
    response = make_search_response(raw_text="這是一段摘要")

    content = normalize_report_content(
        response,
        reason="內容不足",
        suggestion="請補充關鍵字",
    )

    assert content.summary == "這是一段摘要"


def test_normalize_report_content_extracts_sources_and_bullets_from_raw_text():
    response = make_search_response(
        summary="",
        bullets=[],
        sources=[],
        raw_text="這是一段摘要。更多資訊：https://example.com/news",
    )

    content = normalize_report_content(
        response,
        reason="內容不足",
        suggestion="請補充關鍵字",
    )

    assert content.bullets
    assert "https://example.com/news" in content.sources
