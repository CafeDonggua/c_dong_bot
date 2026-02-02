from pathlib import Path

from dongdong_bot.memory_store import MemoryStore


def test_log_report_writes_relative_link(tmp_path: Path):
    store = MemoryStore(str(tmp_path))
    report_path = tmp_path / "reports" / "case.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("# Case", encoding="utf-8")

    log_path = store.log_report("測試案例", report_path, date="2026-02-02")

    content = log_path.read_text(encoding="utf-8")
    assert "[檔案](../reports/case.md)" in content
