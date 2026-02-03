# DongDong Telegram 聊天機器人

以目標導向（GOAP）方式運作的 Telegram 私聊機器人，支援語意回覆、記憶保存與回想。

## 功能

- Telegram 私聊語意回覆
- 記憶保存：自動寫入每日 Markdown 檔案
- 記憶查詢：支援當日 / 指定日期 / 日期區間
- 迭代重複偵測：避免無進展消耗
- 自然語言搜尋整理：產出摘要、重點、來源與查詢資訊的報告

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

```bash
python -m dongdong_bot.main
```

## 記憶檔案位置

記憶檔案會寫入：

```
/data/data/com.termux/files/home/storage/shared/C_Dong_bot
```

檔名格式：

```
YYYY-MM-DD.md
```

## 搜尋報告位置

搜尋報告會寫入：

```
/data/data/com.termux/files/home/storage/shared/C_Dong_bot/reports
```

檔名格式：

```
YYYY-MM-DD-查詢標題.md
```

## 測試

```bash
pytest
```

## 使用示例

- 記憶保存：
  - 「請記住：今天要買牛奶」
- 記憶查詢：
  - 「回想今天的記憶」
  - 「查一下 2026-02-01 到 2026-02-02 的記憶」
- 搜尋報告：
  - 「幫我整理 NVIDIA 最新消息」→ 產出含摘要、重點、來源與查詢資訊的報告檔案
