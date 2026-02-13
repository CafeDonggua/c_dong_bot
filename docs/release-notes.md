# Release Notes

> 本檔僅記錄正式穩定版（main）。  
> 預覽版（beta/rc）請以 GitHub `Pre-release` 與 `docs/release-policy.md` 為準。

## Unreleased (next / 1.1.0 preview)

> 以下為預備版變更摘要，尚未列為穩定版發布內容。

### 重點更新

- 新增自然語句 Cron 分流（每天/每週/每隔 N 單位）並轉為既有 Cron 任務流程
- 單次時間事件維持走既有行程流程，避免誤建重複任務
- `/cron help` 擴充自然語句範例，保留原命令式入口
- 補齊自然語句路由、邊界分流與相容回歸測試

### 驗證摘要

- 核心回歸：`40 passed`（cron + schedule + nl-routing）
- 本次改動檔案 lint：`ruff check` 全綠

## 1.0.0 (2026-02-10)

### 重點更新

- 回歸測試與常見中文句型測試集
- 記憶品質指標與門檻設定
- 記憶刪除/重置管理指令
- 統一 LLM/embedding/search 的 fallback 回覆
- 觀測性：一致 log 與 perf log 觀測點
- 行程可靠性：相對時間解析與重啟持久化測試
- Nanobot 對照報告新增 v1.0 必要條件摘要與人工複核清單
- 文件補齊：.env.example、部署/運行指引

### 測試

- `pytest -q`
- `scripts/run_regression.sh`
