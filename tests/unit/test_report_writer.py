from dongdong_bot.lib.report_content import ReportContent
from dongdong_bot.lib.report_writer import ReportWriter


def test_report_writer_writes_non_empty_content(tmp_path, patch_report_writer_now):
    writer = ReportWriter(str(tmp_path))
    content = ReportContent(
        summary="摘要內容",
        bullets=["重點一"],
        sources=["https://example.com"],
    )

    path = writer.write(
        title="測試報告",
        content=content,
        query_text="測試查詢",
        query_time=patch_report_writer_now,
    )

    text = path.read_text(encoding="utf-8")

    assert "摘要內容" in text
    assert "重點一" in text
    assert "https://example.com" in text
    assert "查詢文字" in text
    assert "查詢時間" in text
