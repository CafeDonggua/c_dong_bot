---

description: "Task list template for feature implementation"
---

# Tasks: 內嵌檢索與快速回覆

**Input**: Design documents from `/specs/003-embedding-fast-replies/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**語言**: 本模板與輸出內容一律使用正體中文
**Tests**: P1 使用者故事必須包含至少一項自動化測試任務；其他故事若無測試，需在規格中說明原因並提供可重複驗證步驟。

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 確認本地執行環境與必要環境變數說明已更新於 specs/003-embedding-fast-replies/quickstart.md
- [x] T002 [P] 彙整效能量測欄位與輸出格式於 src/dongdong_bot/monitoring.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 新增 embedding 設定與環境變數讀取於 src/dongdong_bot/config.py
- [x] T004 [P] 建立 embedding client 介面與基礎呼叫於 src/dongdong_bot/lib/embedding_client.py
- [x] T005 [P] 擴充本地記憶存取結構以支援向量索引於 src/dongdong_bot/memory_store.py
- [x] T006 建立向量相似度工具函式於 src/dongdong_bot/lib/vector_math.py
- [x] T007 更新主流程初始化 embedding 元件於 src/dongdong_bot/main.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 快速直接回覆 (Priority: P1) 🎯 MVP

**Goal**: 一般聊天可直接回覆，不再進入多次循環流程

**Independent Test**: 以單一聊天問題測試不觸發工具且回覆於單輪內完成

### Tests for User Story 1 (REQUIRED) ⚠️

- [x] T008 [P] [US1] 單元測試直接回覆判斷邏輯於 tests/unit/test_direct_reply_policy.py

### Implementation for User Story 1

- [x] T009 [P] [US1] 新增直接回覆決策策略於 src/dongdong_bot/goap.py
- [x] T010 [US1] 將直接回覆分流整合至主流程於 src/dongdong_bot/main.py
- [x] T011 [US1] 補上直接回覆的效能量測與紀錄於 src/dongdong_bot/monitoring.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - 語意記憶檢索輔助回答 (Priority: P2)

**Goal**: 透過語意檢索補強歷史記憶與一致性

**Independent Test**: 提問已記憶內容，回覆能引用歷史資訊；查無結果時提供替代建議

### Tests for User Story 2 (OPTIONAL - provide justification if omitted) ⚠️

- [x] T012 [P] [US2] 單元測試本地向量檢索命中/未命中於 tests/unit/test_embedding_retrieval.py

### Implementation for User Story 2

- [x] T013 [P] [US2] 建立記憶向量寫入流程於 src/dongdong_bot/memory_store.py
- [x] T014 [P] [US2] 建立語意檢索流程與相似度排序於 src/dongdong_bot/memory_store.py
- [x] T015 [US2] 整合記憶檢索回覆與「無相關資訊」提示於 src/dongdong_bot/main.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - 依情境選擇是否調用工具 (Priority: P3)

**Goal**: 僅在必要時觸發工具流程，避免無效多輪循環

**Independent Test**: 對需外部資料問題觸發工具；一般問題不觸發工具

### Tests for User Story 3 (OPTIONAL - provide justification if omitted) ⚠️

- [x] T016 [P] [US3] 單元測試工具調用判斷分流於 tests/unit/test_tool_decision.py

### Implementation for User Story 3

- [x] T017 [P] [US3] 建立工具調用判斷策略於 src/dongdong_bot/goap.py
- [x] T018 [US3] 將工具判斷結果串接回覆流程於 src/dongdong_bot/main.py

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T019 [P] 更新整體效能紀錄欄位與格式於 src/dongdong_bot/monitoring.py
- [x] T020 [P] 更新使用說明與驗收步驟於 specs/003-embedding-fast-replies/quickstart.md
- [x] T021 執行並確認快速驗證流程於 specs/003-embedding-fast-replies/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent but may reuse US1 flow
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Independent but may reuse US1 flow

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- Setup tasks marked [P] can run in parallel
- Foundational tasks T004, T005, T006 can run in parallel
- Tests within each user story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
Task: "單元測試直接回覆判斷邏輯於 tests/unit/test_direct_reply_policy.py"
Task: "新增直接回覆決策策略於 src/dongdong_bot/goap.py"
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
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
