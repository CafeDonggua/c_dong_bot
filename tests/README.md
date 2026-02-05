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
