# Quickstart: DongDong Telegram 聊天機器人

**Date**: 2026-02-02  
**Feature**: /storage/emulated/0/program/python/tg_bot/c_dong_bot/specs/001-telegram-goap-bot/spec.md

## 目標

在本機（Termux）啟動 DongDong，並完成一次對話與記憶保存驗證。

## 先決條件

- 已安裝 Python 3.12
- `.env` 已包含 `OPENAI_API_KEY` 與 `TELEGRAM_BOT_TOKEN`
- 目標記憶路徑可寫入：`/data/data/com.termux/files/home/storage/shared/C_Dong_bot`

## 快速啟動（預期）

> 以下為預期流程，實際指令以實作完成後為準。

1. 建立虛擬環境並安裝依賴
2. 啟動機器人主程式（長輪詢模式）
3. 在 Telegram 私訊 DongDong，輸入測試訊息

## 驗證

- 傳送「請記住：今天要買牛奶」，收到確認回覆
- 查詢「回想今天的記憶」，收到包含該內容的回覆
- 若出現重複無進展迴圈，應在自適應上限內停止並回覆說明
