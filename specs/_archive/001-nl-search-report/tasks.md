---

description: "Task list template for feature implementation"
---

# Tasks: 自然語言搜尋與案例整理

**Input**: Design documents from `/specs/001-nl-search-report/`
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

- [x] T001 確認自然語言搜尋需求與案例格式已記錄於 specs/001-nl-search-report/research.md
- [x] T002 [P] 補充自然語言搜尋相關環境變數說明於 specs/001-nl-search-report/quickstart.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 建立自然語言搜尋請求/回覆資料結構於 src/dongdong_bot/lib/nl_search_schema.py
- [x] T004 [P] 建立搜尋主題摘要器於 src/dongdong_bot/lib/nl_search_topic.py
- [x] T005 [P] 建立案例文件輸出器於 src/dongdong_bot/lib/report_writer.py
- [x] T006 更新記憶存檔結構（memory/reports 分流）於 src/dongdong_bot/memory_store.py
- [x] T007 更新設定讀取（reports 資料夾路徑）於 src/dongdong_bot/config.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 自然語言觸發搜尋彙整 (Priority: P1) 🎯 MVP

**Goal**: 以自然語言輸入即可完成搜尋彙整回覆

**Independent Test**: 輸入一段自然語言需求，回覆包含摘要/重點/來源

### Tests for User Story 1 (REQUIRED) ⚠️

- [x] T008 [P] [US1] 單元測試搜尋主題摘要於 tests/unit/test_nl_search_topic.py
- [x] T009 [P] [US1] 整合測試自然語言搜尋流程於 tests/integration/test_nl_search.py

### Implementation for User Story 1

- [x] T010 [P] [US1] 實作自然語言搜尋流程於 src/dongdong_bot/main.py
- [x] T011 [US1] 串接搜尋主題摘要與搜尋服務於 src/dongdong_bot/main.py
- [x] T012 [US1] 處理無結果回覆與改寫建議於 src/dongdong_bot/lib/search_formatter.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - 生成案例文件並存檔 (Priority: P2)

**Goal**: 將彙整內容輸出為可存取案例文件

**Independent Test**: 產出案例文件並回覆路徑或連結

### Tests for User Story 2 (OPTIONAL - provide justification if omitted) ⚠️

- [x] T013 [P] [US2] 整合測試案例文件輸出於 tests/integration/test_case_report.py

### Implementation for User Story 2

- [x] T014 [P] [US2] 產出案例文件於 src/dongdong_bot/lib/report_writer.py
- [x] T015 [US2] 回覆案例文件連結或路徑於 src/dongdong_bot/main.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - 記憶與整理紀錄分流 (Priority: P3)

**Goal**: 記憶與案例文件分開保存，記憶中有整理紀錄連結

**Independent Test**: 當日記憶檔案內有案例連結紀錄

### Tests for User Story 3 (OPTIONAL - provide justification if omitted) ⚠️

- [x] T016 [P] [US3] 單元測試記憶紀錄連結寫入於 tests/unit/test_memory_log_link.py

### Implementation for User Story 3

- [x] T017 [P] [US3] 將記憶存檔移至 memory 目錄於 src/dongdong_bot/memory_store.py
- [x] T018 [US3] 將案例文件存至 reports 目錄並回填連結於 src/dongdong_bot/memory_store.py

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T019 [P] 更新文件範例與操作說明於 specs/001-nl-search-report/quickstart.md
- [x] T020 [P] 增加錯誤提示可讀性於 src/dongdong_bot/lib/search_formatter.py
- [x] T021 執行並確認快速驗證流程於 specs/001-nl-search-report/quickstart.md

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Independent but may reuse US1/US2 flow

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- Setup tasks marked [P] can run in parallel
- Foundational tasks T004, T005 can run in parallel
- Tests within each user story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
Task: "單元測試搜尋主題摘要於 tests/unit/test_nl_search_topic.py"
Task: "整合測試自然語言搜尋流程於 tests/integration/test_nl_search.py"
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
