---

description: "Task list for Bot 監控提示訊息"
---

# Tasks: Bot 監控提示訊息

**Input**: Design documents from `/specs/002-bot-status-logs/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**語言**: 本模板與輸出內容一律使用正體中文
**Tests**: P1 使用者故事必須包含至少一項自動化測試任務；其他故事若無測試，需在規格中說明原因並提供可重複驗證步驟。

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 建立監控模組檔案骨架於 `src/dongdong_bot/monitoring.py`
- [ ] T002 [P] 建立監控訊息測試檔案骨架於 `tests/unit/test_monitoring.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 設定監控參數常數於 `src/dongdong_bot/config.py`（心跳 30 分鐘、錯誤節流 60 秒）
- [ ] T004 實作監控訊息資料結構與輸出格式於 `src/dongdong_bot/monitoring.py`
- [ ] T005 實作錯誤節流與抑制計數邏輯於 `src/dongdong_bot/monitoring.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 啟動正常提示 (Priority: P1) 🎯 MVP

**Goal**: 啟動完成時輸出一次「正常運行」提示

**Independent Test**: 啟動 bot 並確認 10 秒內輸出一次提示

### Tests for User Story 1 (REQUIRED) ⚠️

- [ ] T006 [P] [US1] 新增啟動提示輸出測試於 `tests/unit/test_monitoring.py`

### Implementation for User Story 1

- [ ] T007 [US1] 新增啟動提示觸發點於 `src/dongdong_bot/main.py`
- [ ] T008 [US1] 連結啟動事件到監控輸出於 `src/dongdong_bot/monitoring.py`

**Checkpoint**: User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - 訊息處理提示 (Priority: P2)

**Goal**: 收到訊息與完成回覆時各輸出一次提示

**Independent Test**: 傳送訊息並確認「已收到訊息」與「已完成回覆」提示皆輸出

### Implementation for User Story 2

- [ ] T009 [US2] 在訊息接收處加入提示觸發於 `src/dongdong_bot/telegram_client.py`
- [ ] T010 [US2] 在回覆完成處加入提示觸發於 `src/dongdong_bot/telegram_client.py`
- [ ] T011 [US2] 更新監控輸出摘要格式以涵蓋收到/回覆事件於 `src/dongdong_bot/monitoring.py`

**Checkpoint**: User Story 2 should be fully functional and testable independently

---

## Phase 5: User Story 3 - 錯誤即時提示 (Priority: P3)

**Goal**: 未處理錯誤時輸出錯誤提示並節流重複輸出

**Independent Test**: 觸發錯誤並確認輸出錯誤提示；重複錯誤不會造成大量輸出

### Implementation for User Story 3

- [ ] T012 [US3] 將錯誤捕捉與監控提示串接於 `src/dongdong_bot/main.py`
- [ ] T013 [US3] 完成錯誤摘要生成與抑制次數顯示於 `src/dongdong_bot/monitoring.py`

**Checkpoint**: User Story 3 should be fully functional and testable independently

---

## Phase 6: User Story 4 - 正常運行心跳提示 (Priority: P4)

**Goal**: 每 30 分鐘輸出一次「仍在運行」提示

**Independent Test**: 連續運行至少 30 分鐘並確認心跳提示輸出

### Implementation for User Story 4

- [ ] T014 [US4] 加入心跳排程與觸發機制於 `src/dongdong_bot/main.py`
- [ ] T015 [US4] 補齊心跳提示摘要輸出於 `src/dongdong_bot/monitoring.py`

**Checkpoint**: User Story 4 should be fully functional and testable independently

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T016 [P] 更新驗證步驟與監控說明於 `/storage/emulated/0/program/python/tg_bot/c_dong_bot/specs/002-bot-status-logs/quickstart.md`
- [ ] T017 依規格檢查敏感資料輸出與訊息單行限制於 `src/dongdong_bot/monitoring.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent of US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Independent of US1/US2
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Independent of US1/US2/US3

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Core monitoring logic before hooks in main/handlers
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- After Foundational phase completes, user stories can run in parallel
- Monitoring output formatting tasks can run in parallel with hook insertion tasks

---

## Parallel Example: User Story 1

```bash
# Launch the P1 test task in parallel with implementation scaffolding:
Task: "新增啟動提示輸出測試於 tests/unit/test_monitoring.py"
Task: "新增啟動提示觸發點於 src/dongdong_bot/main.py"
```

---

## Parallel Example: User Story 2

```bash
Task: "在訊息接收處加入提示觸發於 src/dongdong_bot/telegram_client.py"
Task: "在回覆完成處加入提示觸發於 src/dongdong_bot/telegram_client.py"
```

---

## Parallel Example: User Story 3

```bash
Task: "將錯誤捕捉與監控提示串接於 src/dongdong_bot/main.py"
Task: "完成錯誤摘要生成與抑制次數顯示於 src/dongdong_bot/monitoring.py"
```

---

## Parallel Example: User Story 4

```bash
Task: "加入心跳排程與觸發機制於 src/dongdong_bot/main.py"
Task: "補齊心跳提示摘要輸出於 src/dongdong_bot/monitoring.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories
