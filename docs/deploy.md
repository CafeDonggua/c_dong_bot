# 部署與運行指引

## 環境需求

- Python 3.12
- Termux 環境
- 已建立 Telegram Bot 並取得 Token
- 已取得 OpenAI API Key

## 佈署步驟

1. 進入專案目錄：

```bash
cd /storage/emulated/0/program/python/tg_bot/c_dong_bot
```

2. 安裝相依套件：

```bash
pip install -r requirements.txt
```

3. 設定 `.env`（必須放在指定絕對路徑）：

```
/data/data/com.termux/files/home/storage/shared/program/python/tg_bot/c_dong_bot/.env
```

4. 啟動 bot：

```bash
PYTHONPATH=src python -m dongdong_bot.main
```

## 例行檢查

- 執行測試：

```bash
PYTHONPATH=src pytest
```

- 執行回歸測試：

```bash
scripts/run_regression.sh
```

## 監控與錯誤處理

- 可透過 console log 觀測核心流程、錯誤事件與 perf log。
- 若需詳細效能資訊，將 `.env` 中的 `PERF_LOG=1`。
