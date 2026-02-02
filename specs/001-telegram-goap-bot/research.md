# Phase 0 Research: DongDong Telegram 聊天機器人

**Date**: 2026-02-02  
**Feature**: /storage/emulated/0/program/python/tg_bot/c_dong_bot/specs/001-telegram-goap-bot/spec.md

## Decision 1: Telegram Bot 框架

- **Decision**: 使用 python-telegram-bot（長輪詢模式）
- **Rationale**: 以單機 Termux 執行為主，長輪詢不需公開網域與 Webhook；
  API 直覺、社群成熟、易於測試。
- **Alternatives considered**: aiogram（需要 async 設計與事件回圈管理）；
  Webhook 模式（需要公開端點或反向代理）。

## Decision 2: OpenAI API 客戶端

- **Decision**: 使用官方 OpenAI Python SDK
- **Rationale**: 與模型相容度高、錯誤處理一致、更新與維護成本較低。
- **Alternatives considered**: 自行封裝 HTTP 呼叫（彈性高但維護成本高）。

## Decision 3: 記憶儲存格式

- **Decision**: 以每日 Markdown 檔案保存（`YYYY-MM-DD.md`）
- **Rationale**: 滿足需求、可讀性高、便於手動檢視與備份。
- **Alternatives considered**: SQLite（更結構化但超出 MVP 需求）。

## Decision 4: GOAP（目標導向）執行流程

- **Decision**: 每次回覆前建立「目標 → 行動 → 觀察」循環，若偵測無進展重複則自動停止。
- **Rationale**: 符合需求的行為模式，並可控成本（避免無限迴圈）。
- **Alternatives considered**: 靜態規則判斷（不符合需求）。

## Decision 5: 測試策略

- **Decision**: 使用 pytest，核心邏輯可獨立測試，Telegram/ OpenAI 以 mock/stub 測試
- **Rationale**: 符合憲章「可測試性優先」與 P1 自動化測試要求。
- **Alternatives considered**: 僅手動測試（不符合憲章）。
