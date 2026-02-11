# 測試與回歸清單

## 基本執行

```bash
pytest
```

## 回歸測試重點

- 行程新增/查詢/取消（`tests/test_schedule_flow.py`）
- 允許名單行為（`tests/test_access_control.py`）
- 記憶保存/查詢/語意搜尋（`tests/unit/test_memory_store.py` 等）
- 搜尋整理與報告寫入（`tests/integration/test_case_report.py`）
- `/cron` 任務建立/管理/重啟恢復（`tests/unit/test_cron_*.py`, `tests/integration/test_cron_*.py`）

## 命名慣例

- `/cron` 相關單元測試檔案命名為 `tests/unit/test_cron_<feature>.py`
- `/cron` 相關整合測試檔案命名為 `tests/integration/test_cron_<feature>.py`
- 跨故事回歸測試命名為 `tests/integration/test_cron_regression_suite.py`
