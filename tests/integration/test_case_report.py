from pathlib import Path

from dongdong_bot.lib.report_content import ReportContent
from dongdong_bot.lib.report_writer import ReportWriter


def test_case_report_written(tmp_path: Path):
    writer = ReportWriter(str(tmp_path))

    report = writer.write(
        title="測試案例",
        content=ReportContent(
            summary="摘要",
            bullets=["重點"],
            sources=["https://example.com"],
        ),
    )

    assert report.exists()
    assert report.name.endswith("-測試案例.md")
    content = report.read_text(encoding="utf-8")
    assert "測試案例" in content
