# Implementation Plan: Bot 監控提示訊息

**Branch**: `002-bot-status-logs` | **Date**: 2026-02-02 | **Spec**: /storage/emulated/0/program/python/tg_bot/c_dong_bot/specs/002-bot-status-logs/spec.md
**Input**: Feature specification from `/specs/002-bot-status-logs/spec.md`
**語言**: 本模板與輸出內容一律使用正體中文

## Summary

本功能在 bot 端輸出監控提示：啟動成功提示、訊息接收/回覆完成提示、錯誤提示，以及每 30 分鐘一次的心跳提示，並加入重複錯誤節流以避免大量輸出。

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: python-telegram-bot, openai, python-dotenv  
**Storage**: 檔案（Markdown 記憶存檔）  
**Testing**: pytest  
**Target Platform**: Termux（Android 使用者空間）  
**Project Type**: single  
**Performance Goals**: 監控提示在事件發生後 5 秒內輸出  
**Constraints**: 監控訊息需單行簡短、避免敏感資料、避免重複輸出噪音  
**Scale/Scope**: 單一 bot 執行個體、單一執行環境

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- MVP 優先：P1 使用者故事可獨立交付與驗證，且不依賴未實作功能
- 可測試性：核心邏輯可在隔離環境測試；P1 至少一項自動化測試；其餘有可重複驗證步驟
- 品質門檻：變更會更新驗收情境與驗證步驟，並通過既有測試
- 不過度設計：新增複雜度已記錄理由與更簡替代方案
- 正體中文一致：規格、計畫、任務、文件與對外訊息均為正體中文

**Result**: Pass

## Project Structure

### Documentation (this feature)

```text
specs/002-bot-status-logs/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
└── dongdong_bot/
    ├── __init__.py
    ├── config.py
    ├── goap.py
    ├── main.py
    ├── memory_store.py
    ├── telegram_client.py
    └── lib/

tests/
```

**Structure Decision**: 單一 Python 專案結構（src/ 與 tests/），與現有程式一致。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 無 | 無 | 無 |

## Phase 0: Outline & Research

### Research Tasks

- 釐清監控訊息的最小事件集合（啟動、收到訊息、回覆完成、錯誤、心跳）
- 定義錯誤重複輸出的節流策略，以符合「避免大量重複輸出」需求

### Output: /storage/emulated/0/program/python/tg_bot/c_dong_bot/specs/002-bot-status-logs/research.md

## Phase 1: Design & Contracts

### Data Model

- 產出監控訊息與錯誤事件的資料模型，含欄位、關係與驗證規則

### Contracts

- 產出監控事件的契約（OpenAPI），描述事件欄位結構與允許值

### Quickstart

- 提供最短步驟確認監控提示是否如規格輸出

### Agent Context Update

- 執行更新腳本以同步規格與技術脈絡至 agent context

## Phase 1 Constitution Check (post-design)

- MVP 優先：通過
- 可測試性：通過
- 品質門檻：通過
- 不過度設計：通過
- 正體中文一致：通過

**Result**: Pass
