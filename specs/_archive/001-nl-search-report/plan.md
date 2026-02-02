# Implementation Plan: 自然語言搜尋與案例整理

**Branch**: `001-nl-search-report` | **Date**: 2026-02-02 | **Spec**: /storage/emulated/0/program/python/tg_bot/c_dong_bot/specs/001-nl-search-report/spec.md
**Input**: Feature specification from `/specs/001-nl-search-report/spec.md`
**語言**: 本模板與輸出內容一律使用正體中文

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.
**Status**: Done  
**Completed**: 2026-02-02

## Summary

本功能讓使用者以自然語言提出搜尋與整理需求，系統先萃取搜尋主題、完成網路彙整，並在需要時產出案例文件，同時調整記憶檔案結構以分流保存與紀錄連結。

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: python-telegram-bot、openai、python-dotenv  
**Storage**: 本地檔案（Markdown 記憶存檔 + 案例檔案）  
**Testing**: pytest  
**Target Platform**: 本地或自架環境（Telegram Bot 執行）  
**Project Type**: single  
**Performance Goals**: 90% 自然語言搜尋在 15 秒內回覆  
**Constraints**: 記憶與案例需分開保存，且記憶內需保留案例連結  
**Scale/Scope**: 個人助理場景（私聊或小型群組）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- MVP 優先：通過（P1 僅需自然語言搜尋彙整即可獨立交付）
- 可測試性：通過（P1 可用單元/整合測試驗證）
- 品質門檻：通過（規格已定義驗收與測試策略）
- 不過度設計：通過（不引入多平台需求）
- 正體中文一致：通過

## Project Structure

### Documentation (this feature)

```text
specs/001-nl-search-report/
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
    ├── config.py
    ├── goap.py
    ├── main.py
    ├── memory_store.py
    ├── monitoring.py
    ├── telegram_client.py
    └── lib/

tests/
```

**Structure Decision**: 單一專案結構，功能集中於 `src/dongdong_bot/`，測試置於 `tests/`。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

無。

## Phase 0: Outline & Research

- 研究自然語言意圖萃取與搜尋主題摘要的常見做法
- 研究搜尋彙整輸出轉成案例文件的格式最佳實務
- 研究本地檔案分流保存（memory / reports）與連結紀錄方式

**輸出**: `specs/001-nl-search-report/research.md`

## Phase 1: Design & Contracts

- 建立資料模型：自然語言請求、搜尋主題、案例文件、記憶紀錄
- 定義介面契約：自然語言搜尋彙整、案例生成、記憶紀錄
- 產出快速開始文件：含必要環境變數、執行與測試步驟
- 更新 agent context：執行 `update-agent-context.sh`

**輸出**:
- `specs/001-nl-search-report/data-model.md`
- `specs/001-nl-search-report/contracts/*`
- `specs/001-nl-search-report/quickstart.md`
- agent-specific context file

## Constitution Check (Post-Design)

確認設計輸出後未引入額外複雜度，且仍符合 MVP 優先、可測試性與正體中文一致要求。狀態：通過。

## Phase 2: Planning

- 由 `/speckit.tasks` 產生可執行的工作項目與測試清單
