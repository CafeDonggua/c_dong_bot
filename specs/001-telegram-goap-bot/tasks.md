---

description: "Task list for DongDong Telegram 聊天機器人"
---

# Tasks: DongDong Telegram 聊天機器人

**Input**: Design documents from `/specs/001-telegram-goap-bot/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**語言**: 本模板與輸出內容一律使用正體中文
**Tests**: P1 使用者故事必須包含至少一項自動化測試任務；其他故事若無測試，需在規格中說明原因並提供可重複驗證步驟。

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure in src/dongdong_bot/ and tests/ per plan.md
- [ ] T002 Initialize Python project config in pyproject.toml and .env.example
- [ ] T003 [P] Add dependency definitions in pyproject.toml for python-telegram-bot, openai, python-dotenv, pytest
- [ ] T004 [P] Add basic package scaffold in src/dongdong_bot/__init__.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Implement configuration loader in src/dongdong_bot/config.py (讀取 .env 與必要設定)
- [ ] T006 Implement Telegram client wrapper in src/dongdong_bot/telegram_client.py (長輪詢輸入/輸出介面)
- [ ] T007 Implement GOAP 核心流程骨架 in src/dongdong_bot/goap.py (目標→行動→觀察循環介面)
- [ ] T008 Implement迭代重複偵測介面 in src/dongdong_bot/goap.py (停止條件與回覆原因)
- [ ] T009 Implement memory store 基礎介面 in src/dongdong_bot/memory_store.py (讀寫每日檔案與查詢)
- [ ] T010 Add shared utilities in src/dongdong_bot/lib/ (日期格式與路徑處理)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 與 DongDong 對話並得到語意回覆 (Priority: P1) 🎯 MVP

**Goal**: 使用者在 Telegram 私聊輸入需求並收到語意一致回覆

**Independent Test**: 私訊輸入需求，收到清楚可操作回覆

### Tests for User Story 1 (REQUIRED) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Unit test GOAP 基本流程 in tests/unit/test_goap.py
- [ ] T012 [P] [US1] Integration test 基本回覆流程 in tests/integration/test_basic_reply.py

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement GOAP 目標解析 in src/dongdong_bot/goap.py
- [ ] T014 [P] [US1] Implement GOAP 行動產生與觀察回圈 in src/dongdong_bot/goap.py
- [ ] T015 [US1] Connect Telegram input to GOAP in src/dongdong_bot/main.py
- [ ] T016 [US1] Implement reply formatter in src/dongdong_bot/telegram_client.py

**Checkpoint**: User Story 1 fully functional and independently testable

---

## Phase 4: User Story 2 - 讓 DongDong 記住事情並保存 (Priority: P2)

**Goal**: 使用者提出記憶需求後，內容被保存並回覆確認

**Independent Test**: 傳送「請記住：…」，收到確認回覆，且檔案存在

### Tests for User Story 2 (OPTIONAL - provide justification if omitted) ⚠️

- [ ] T017 [P] [US2] Unit test 記憶寫入 in tests/unit/test_memory_store.py

### Implementation for User Story 2

- [ ] T018 [P] [US2] Implement 記憶需求偵測 in src/dongdong_bot/goap.py
- [ ] T019 [P] [US2] Implement 記憶寫入流程 in src/dongdong_bot/memory_store.py
- [ ] T020 [US2] Wire 記憶流程到主迴圈 in src/dongdong_bot/main.py
- [ ] T021 [US2] Add 使用者確認回覆 in src/dongdong_bot/telegram_client.py

**Checkpoint**: User Story 2 works independently

---

## Phase 5: User Story 3 - 依需求調用記憶 (Priority: P3)

**Goal**: 使用者要求回顧記憶時可查詢並回覆

**Independent Test**: 先寫入記憶後查詢，回覆包含內容

### Tests for User Story 3 (OPTIONAL - provide justification if omitted) ⚠️

- [ ] T022 [P] [US3] Unit test 記憶查詢 in tests/unit/test_memory_store.py

### Implementation for User Story 3

- [ ] T023 [P] [US3] Implement 記憶查詢（含日期/區間） in src/dongdong_bot/memory_store.py
- [ ] T024 [US3] Implement 回憶需求解析 in src/dongdong_bot/goap.py
- [ ] T025 [US3] Wire 查詢流程到主迴圈 in src/dongdong_bot/main.py
- [ ] T026 [US3] Add 回憶回覆格式 in src/dongdong_bot/telegram_client.py

**Checkpoint**: All user stories independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T027 [P] Add README usage notes in README.md
- [ ] T028 [P] Add quickstart validation notes in specs/001-telegram-goap-bot/quickstart.md
- [ ] T029 Run formatting/lint (if configured) and update docs

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can proceed in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational - Depends on memory store foundation
- **User Story 3 (P3)**: Can start after Foundational - Uses memory store and query logic

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- GOAP logic before wiring main loop
- Memory store before query/response wiring
- Story complete before moving to next priority

### Parallel Opportunities

- Phase 1 tasks marked [P] can run in parallel
- Phase 2 tasks marked [P] can run in parallel (once scaffold exists)
- Tests and models within a story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch tests for User Story 1 together:
Task: "Unit test GOAP 基本流程 in tests/unit/test_goap.py"
Task: "Integration test 基本回覆流程 in tests/integration/test_basic_reply.py"

# Launch GOAP logic tasks together:
Task: "Implement GOAP 目標解析 in src/dongdong_bot/goap.py"
Task: "Implement GOAP 行動產生與觀察回圈 in src/dongdong_bot/goap.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently
