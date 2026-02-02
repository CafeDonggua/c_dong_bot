# Data Model: Bot 監控提示訊息

**Date**: 2026-02-02
**Feature**: /storage/emulated/0/program/python/tg_bot/c_dong_bot/specs/002-bot-status-logs/spec.md

## Entity: 監控訊息

- **Purpose**: 用於在 bot 端輸出運行狀態與錯誤的單行提示。
- **Fields**:
  - **id**: 唯一識別（可為時間戳 + 序號）
  - **type**: 類型（startup | received | replied | error | heartbeat）
  - **timestamp**: 事件發生時間（本地時間）
  - **summary**: 簡短摘要（不含敏感資料）
  - **suppressed_count**: 可選，表示同類錯誤被抑制的次數
- **Validation Rules**:
  - summary 必須單行且長度受控
  - type 必須為允許值之一
  - 監控訊息不得包含金鑰、Token 或使用者訊息內容

## Entity: 錯誤事件

- **Purpose**: 代表一次錯誤與其節流狀態，用於避免重複輸出。
- **Fields**:
  - **signature**: 錯誤摘要鍵（同類錯誤的判定依據）
  - **first_seen_at**: 首次出現時間
  - **last_seen_at**: 最近一次出現時間
  - **suppressed_count**: 被抑制的次數
- **Relationships**:
  - 錯誤事件可產生監控訊息（type = error）
- **State Transitions**:
  - 新錯誤 → 立即輸出並建立錯誤事件
  - 重複錯誤（在節流窗口內）→ 不輸出，累加 suppressed_count
  - 重複錯誤（超過節流窗口）→ 輸出並帶出 suppressed_count，重置計數
