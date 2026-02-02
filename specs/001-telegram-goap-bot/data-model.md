# Phase 1 Data Model: DongDong Telegram 聊天機器人

**Date**: 2026-02-02  
**Feature**: /storage/emulated/0/program/python/tg_bot/c_dong_bot/specs/001-telegram-goap-bot/spec.md

## Entity: 記憶條目 (MemoryEntry)

**Purpose**: 保存使用者要求記住的內容與上下文

**Fields**:
- id: 唯一識別碼
- date: 記憶日期（YYYY-MM-DD）
- content: 記憶內容（原意可讀）
- source_message: 觸發記憶的原始訊息（可選）
- tags: 可選標籤（由語意推斷或使用者指定）
- created_at: 建立時間

**Validation**:
- content 需非空且保留原意
- date 必須符合 YYYY-MM-DD

## Entity: 記憶檔案 (MemoryFile)

**Purpose**: 每日記憶集合的檔案載體

**Fields**:
- date: 檔案日期（YYYY-MM-DD）
- path: 檔案絕對路徑
- entries: 記憶條目列表

**Relationships**:
- 一個 MemoryFile 包含多個 MemoryEntry

**Validation**:
- path 必須位於 `/data/data/com.termux/files/home/storage/shared/C_Dong_bot`

## Entity: 對話目標 (Goal)

**Purpose**: 每次對話中欲達成的目標

**Fields**:
- id
- description
- status: pending | active | achieved | blocked
- created_at

## Entity: 行動計畫 (ActionPlan)

**Purpose**: 目標導向的行動步驟集合

**Fields**:
- id
- goal_id
- steps: 行動步驟列表
- iteration_count
- last_observation

**Relationships**:
- 一個 Goal 對應一個或多個 ActionPlan

**Validation**:
- iteration_count 需可用於偵測重複迴圈

## Entity: 觀察 (Observation)

**Purpose**: 每次迭代的結果記錄，用於判斷是否有進展

**Fields**:
- id
- goal_id
- summary
- is_progress: 是否有進展
- created_at

**Relationships**:
- Goal 對應多筆 Observation
