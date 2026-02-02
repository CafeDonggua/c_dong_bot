---

description: "Task list template for feature implementation"
---

# Tasks: 網路搜尋彙整

**Input**: Design documents from `/specs/001-web-search-summary/`
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

- [x] T001 確認搜尋模型與回覆格式需求已更新於 specs/001-web-search-summary/research.md
- [x] T002 [P] 補充搜尋功能相關環境變數說明於 specs/001-web-search-summary/quickstart.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 建立搜尋請求/回覆的資料結構於 src/dongdong_bot/lib/search_schema.py
- [x] T004 [P] 建立搜尋服務介面與錯誤封裝於 src/dongdong_bot/lib/search_client.py
- [x] T005 [P] 建立統一回覆格式組裝器於 src/dongdong_bot/lib/search_formatter.py
- [x] T006 更新設定讀取（搜尋 API Key 或模型配置）於 src/dongdong_bot/config.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 關鍵字搜尋彙整 (Priority: P1) 🎯 MVP

**Goal**: 以關鍵字搜尋網路資料並產出摘要、重點與來源

**Independent Test**: 使用單一主題可取得摘要與來源，無結果時有清楚提示

### Tests for User Story 1 (REQUIRED) ⚠️

- [x] T007 [P] [US1] 單元測試搜尋回覆格式於 tests/unit/test_search_formatter.py
- [x] T008 [P] [US1] 整合測試關鍵字搜尋流程於 tests/integration/test_keyword_search.py

### Implementation for User Story 1

- [x] T009 [P] [US1] 實作關鍵字搜尋流程於 src/dongdong_bot/main.py
- [x] T010 [US1] 串接搜尋服務與回覆格式組裝於 src/dongdong_bot/main.py
- [x] T011 [US1] 處理無結果與錯誤回覆於 src/dongdong_bot/main.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - 連結摘要彙整 (Priority: P2)

**Goal**: 以連結內容產出摘要、重點與來源

**Independent Test**: 單一連結可產出摘要與來源，連結不可用時回覆替代建議

### Tests for User Story 2 (OPTIONAL - provide justification if omitted) ⚠️

- [x] T012 [P] [US2] 整合測試連結摘要流程於 tests/integration/test_link_summary.py

### Implementation for User Story 2

- [x] T013 [P] [US2] 實作連結摘要流程於 src/dongdong_bot/main.py
- [x] T014 [US2] 串接摘要回覆格式組裝於 src/dongdong_bot/main.py
- [x] T015 [US2] 處理連結不可用錯誤回覆於 src/dongdong_bot/main.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - 統一回覆格式 (Priority: P3)

**Goal**: 搜尋與連結摘要回覆格式一致

**Independent Test**: 任何搜尋/摘要輸出均包含摘要、重點、來源

### Tests for User Story 3 (OPTIONAL - provide justification if omitted) ⚠️

- [x] T016 [P] [US3] 單元測試格式一致性於 tests/unit/test_search_formatter.py

### Implementation for User Story 3

- [x] T017 [US3] 整理統一輸出格式與欄位順序於 src/dongdong_bot/lib/search_formatter.py

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T018 [P] 更新文件與範例輸入於 specs/001-web-search-summary/quickstart.md
- [x] T019 [P] 增加錯誤訊息可讀性與提示於 src/dongdong_bot/lib/search_formatter.py
- [x] T020 執行並確認快速驗證流程於 specs/001-web-search-summary/quickstart.md

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
Task: "單元測試搜尋回覆格式於 tests/unit/test_search_formatter.py"
Task: "整合測試關鍵字搜尋流程於 tests/integration/test_keyword_search.py"
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
