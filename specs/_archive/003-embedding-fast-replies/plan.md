# Implementation Plan: 內嵌檢索與快速回覆

**Branch**: `003-embedding-fast-replies` | **Date**: 2026-02-02 | **Spec**: /storage/emulated/0/program/python/tg_bot/c_dong_bot/specs/003-embedding-fast-replies/spec.md
**Input**: Feature specification from `/specs/003-embedding-fast-replies/spec.md`
**語言**: 本模板與輸出內容一律使用正體中文

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

**Status**: Done  
**Completed**: 2026-02-02

## Summary

本功能聚焦於「避免每次都進入多步驟循環」與「導入語意記憶檢索」：在一般聊天可直接回覆、在有記憶需求時以在地記憶檢索輔助，並在必要時才觸發工具流程，以達成回覆時間中位數 < 2 秒與 95% 回覆 < 5 秒的目標。

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: python-telegram-bot、openai、python-dotenv  
**Storage**: 本地檔案（Markdown 記憶存檔）  
**Testing**: pytest  
**Target Platform**: 本地或自架環境（Telegram Bot 執行）  
**Project Type**: single  
**Performance Goals**: 一般聊天首次回覆中位數 < 2 秒、95% 回覆 < 5 秒  
**Constraints**: 避免每次互動多輪循環；不需即時外部資料時優先本地檢索  
**Scale/Scope**: 個人助理場景（私聊或小型群組）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- MVP 優先：通過（P1 僅需直接回覆判斷即可獨立交付）
- 可測試性：通過（P1 可用單元/整合測試驗證）
- 品質門檻：通過（規格已定義驗收與測試策略）
- 不過度設計：通過（不引入多平台或企業級需求）
- 正體中文一致：通過

## Project Structure

### Documentation (this feature)

```text
specs/003-embedding-fast-replies/
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

- 研究 Telegram Bot 更新機制（long polling vs webhook）與回覆延遲相關最佳實務
- 研究 OpenAI embeddings（text-embedding-3-small）與向量檢索基本原則（相似度、向量資料保存）
- 釐清「本地 RAG」在個人助理場景的取捨（本地索引 vs 外部向量服務）

**輸出**: `specs/003-embedding-fast-replies/research.md`

## Phase 1: Design & Contracts

- 建立資料模型：使用者訊息、記憶內容、向量索引、檢索結果、工具調用決策
- 定義介面契約：對應「接收訊息 → 回覆」與「記憶檢索」的 API 介面
- 產出快速開始文件：含必要環境變數、執行與測試步驟
- 更新 agent context：執行 `update-agent-context.sh`

**輸出**:
- `specs/003-embedding-fast-replies/data-model.md`
- `specs/003-embedding-fast-replies/contracts/*`
- `specs/003-embedding-fast-replies/quickstart.md`
- agent-specific context file

## Constitution Check (Post-Design)

確認設計輸出後未引入額外複雜度，且仍符合 MVP 優先、可測試性與正體中文一致要求。狀態：通過。

## Phase 2: Planning

- 由 `/speckit.tasks` 產生可執行的工作項目與測試清單
