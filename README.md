# DongDong Telegram 聊天機器人

以目標導向（GOAP）方式運作的 Telegram 私聊機器人，支援語意回覆、記憶保存與回想。

## 功能

- Telegram 私聊語意回覆
- 記憶保存：自動寫入每日 Markdown 檔案
- 記憶查詢：支援當日 / 指定日期 / 日期區間
- 行程管理：新增 / 查詢 / 修改 / 取消行程並發送提醒
- 迭代重複偵測：避免無進展消耗
- 自然語言搜尋整理：產出摘要、重點、來源與查詢資訊的報告
- 技能啟用/停用：支援基本技能控管
- 允許名單：可限制可使用聊天助理的帳號

## 專案結構

- `src/`：主要程式碼
- `tests/`：自動化測試
- `data/`：執行期資料（記憶、報告、行程、提醒、索引；已加入 .gitignore）
- `resources/`：非程式碼資源（技能定義、規範文件）

## 技術架構

- **語意路由層**：`IntentRouter` 依 `capabilities.yaml` 能力描述做語意判斷，避免大量關鍵字判斷式
- **對話決策層**：`GoapEngine` 負責回覆策略與迭代收斂
- **記憶系統**：Markdown 記憶 + JSONL 向量索引，支援語意檢索與摘要整理
- **行程與提醒**：行程持久化 + 提醒排程（Telegram job queue 定期檢查）
- **搜尋整理**：自然語言主題抽取 + 搜尋摘要 + 報告輸出

## 模組分層

- `src/dongdong_bot/agent/`：對話決策、記憶、技能、行程與允許名單
- `src/dongdong_bot/channels/`：聊天通道整合（目前為 Telegram）
- `src/dongdong_bot/cron/`：提醒與排程觸發

## 語意路由（能力描述式）

語意路由改以能力描述進行判斷，能力清單位於：

- `src/dongdong_bot/agent/capabilities.yaml`

目前檔案內容為 JSON（YAML 相容），新增功能時請新增一筆能力描述，欄位包含：

- `name`：能力名稱（需唯一）
- `description`：能力說明
- `required_inputs`：必要輸入欄位
- `example_requests`：自然語言範例
- `clarifications`：缺少必要資訊時的澄清提問

新增後用自然語言測試（不需加入關鍵字清單）。

## 環境需求

- Python 3.12
- Termux 環境
- 已建立 Telegram Bot 並取得 Token
- 已取得 OpenAI API Key

## 設定

1. 安裝相依套件：

```bash
pip install -r requirements.txt
```

2. 設定 `.env`（必須放在指定絕對路徑）：

```
/data/data/com.termux/files/home/storage/shared/program/python/tg_bot/c_dong_bot/.env
```

內容範例如下：

```
OPENAI_API_KEY=your_openai_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

## 啟動

建議使用 `PYTHONPATH=src` 確保模組載入正常：

```bash
PYTHONPATH=src python -m dongdong_bot.main
```

## 記憶檔案位置

記憶檔案會寫入：

```
data/memory
```

檔名格式：

```
YYYY-MM-DD.md
```

## 搜尋報告位置

搜尋報告會寫入：

```
data/reports
```

檔名格式：

```
YYYY-MM-DD-查詢標題.md
```

## 行程與提醒檔案位置

行程與提醒會寫入：

```
data/schedules.json
data/reminders.json
```

## 允許名單位置

允許名單預設路徑：

```
data/allowlist.json
```

範例格式：

```json
[
  {"user_id": "123456789", "channel_type": "telegram"}
]
```

## 測試

```bash
PYTHONPATH=src pytest
```

## 使用示例

- 記憶保存：
  - 「請記住：今天要買牛奶」
- 記憶查詢：
  - 「回想今天的記憶」
  - 「查一下 2026-02-01 到 2026-02-02 的記憶」
- 行程新增：
  - 「幫我記錄明天 10:00 開會」
- 行程查詢：
  - 「我有哪些行程」
- 搜尋報告：
  - 「幫我整理 NVIDIA 最新消息」→ 產出含摘要、重點、來源與查詢資訊的報告檔案

## 管理指令

- `/skill list`：列出技能清單
- `/skill enable <name>`：啟用技能
- `/skill disable <name>`：停用技能
- `/allowlist list`：列出允許名單
- `/allowlist add <user_id> [channel]`：加入允許名單
- `/allowlist remove <user_id> [channel]`：移除允許名單

## Agent Skills

本專案的技能定義集中於 `resources/skills/`，每個技能以目錄 + `SKILL.md` 方式描述：

- `resources/skills/README.md`：技能清單與用途摘要
- `resources/skills/SCHEMA.md`：技能格式與必要欄位規範
