# Implementation Plan: DongDong Telegram 聊天機器人

**Branch**: `001-telegram-goap-bot` | **Date**: 2026-02-02 | **Spec**: /storage/emulated/0/program/python/tg_bot/c_dong_bot/specs/001-telegram-goap-bot/spec.md
**Input**: Feature specification from `/specs/001-telegram-goap-bot/spec.md`
**語言**: 本模板與輸出內容一律使用正體中文

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.
**Status**: Done  
**Completed**: 2026-02-02

## Summary

建立 DongDong Telegram 私聊機器人，提供語意回覆、可記憶與回想、且以目標導向
迭代（GOAP）執行。記憶以每日 Markdown 檔案保存於指定路徑，並加入迴圈重複
偵測以避免無進展浪費 token。技術方案採用 Python 3.12、長輪詢模式、以及
官方 OpenAI SDK。

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: python-telegram-bot, openai, python-dotenv  
**Storage**: 本機檔案系統（每日 Markdown 檔案）  
**Testing**: pytest  
**Target Platform**: Android Termux（本機長輪詢）
**Project Type**: single  
**Performance Goals**: 回覆延遲平均 < 5 秒、記憶讀寫 < 100ms（本機）  
**Constraints**: 必須避免長時間無回覆；記憶檔案固定路徑；私聊單一使用者  
**Scale/Scope**: 單一使用者、低併發（同時 1-2 對話）  

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- MVP 優先：P1 使用者故事可獨立交付與驗證，且不依賴未實作功能
- 可測試性：核心邏輯可在隔離環境測試；P1 至少一項自動化測試；其餘有可重複驗證步驟
- 品質門檻：變更會更新驗收情境與驗證步驟，並通過既有測試
- 不過度設計：新增複雜度已記錄理由與更簡替代方案
- 正體中文一致：規格、計畫、任務、文件與對外訊息均為正體中文

**Gate Status**: PASS

## Project Structure

### Documentation (this feature)

```text
specs/001-telegram-goap-bot/
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
├── dongdong_bot/
│   ├── __init__.py
│   ├── config.py
│   ├── goap.py
│   ├── memory_store.py
│   ├── telegram_client.py
│   └── main.py

tests/
├── unit/
│   ├── test_goap.py
│   └── test_memory_store.py
└── integration/
    └── test_basic_reply.py
```

**Structure Decision**: 單一專案結構，核心邏輯集中於 `src/dongdong_bot/`，測試依
單元與整合分層。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |
