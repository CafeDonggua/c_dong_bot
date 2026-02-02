# Feature Specification: DongDong Telegram 聊天機器人

**Feature Branch**: `001-telegram-goap-bot`  
**Created**: 2026-02-02  
**Status**: Done  
**Input**: User description: "建立一個 Telegram 的聊天機器人，叫做DongDong 能夠根據我的語意回覆我訊息 使用python 3.12 使用openai api 的gpt-5-mini 與Telegram的Bot token 兩者api已經放在.env裡面，分別是OPENAI_API_KEY與TELEGRAM_BOT_TOKEN 我想要這個聊天機器人能夠有記憶功能 當聊天時我有提出帶有讓bot記住某些事情的需求的語意時 會在/data/data/com.termux/files/home/storage/shared/C_Dong_bot路徑下建立今天的記憶檔案 檔名以YYYY-MM-DD.md儲存 也能依照我的需求去調用記憶 另外，我希望這個機器人的執行模式依照Goal Oriented Action Planning來進行 並非是一堆if判斷我想做甚麼 而是讓ai去理解、思考、執行、觀察 反覆迭代直到達成我想要的目標"
**語言**: 本模板與輸出內容一律使用正體中文

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 與 DongDong 對話並得到語意回覆 (Priority: P1)

使用者在 Telegram 私訊 DongDong，描述需求或問題，DongDong 需理解語意並回覆。

**Why this priority**: 這是最基本的價值交付，沒有它就無法構成可用的 MVP。

**Independent Test**: 在 Telegram 私訊輸入一段需求，DongDong 於合理時間內給出
語意一致的回覆，且回覆可被使用者理解與採用。

**Acceptance Scenarios**:

1. **Given** 使用者私訊一句需求，**When** DongDong 回覆，**Then** 回覆內容與需求語意一致
2. **Given** 使用者提出澄清問題，**When** DongDong 回覆，**Then** 提供清楚可操作的回答

---

### User Story 2 - 讓 DongDong 記住事情並保存 (Priority: P2)

使用者在對話中提出要機器人記住的事項，DongDong 需將內容保存並回覆確認。

**Why this priority**: 記憶是核心差異功能，但需在基本對話可用後再加入。

**Independent Test**: 傳送一段「請記住」內容，DongDong 回覆確認且可在後續被查詢。

**Acceptance Scenarios**:

1. **Given** 使用者提出記憶需求，**When** DongDong 回覆，**Then** 回覆確認已記住內容
2. **Given** 使用者稍後要求回想，**When** DongDong 回覆，**Then** 回覆包含已保存的內容

---

### User Story 3 - 依需求調用記憶 (Priority: P3)

使用者在對話中要求查詢或回顧已記住的事項，DongDong 需回覆相關記憶內容。

**Why this priority**: 讓記憶具備可用性，形成可持續互動的價值。

**Independent Test**: 先存入記憶，再要求回顧指定主題，DongDong 回覆對應記憶。

**Acceptance Scenarios**:

1. **Given** 已有記憶內容，**When** 使用者要求回顧，**Then** DongDong 回覆相關記憶

---

### Edge Cases

- 使用者提出模糊或含糊的記憶需求時，DongDong 會先詢問確認
- 使用者要求回憶但不存在相關記憶時，DongDong 明確回覆找不到

## 測試與驗證策略 *(mandatory)*

- **自動化測試範圍**: P1 基本對話與語意回覆流程至少一項自動化測試
- **手動驗證步驟**: 記住與回想流程以可重複的操作步驟驗證
- **無法自動化原因**: 若涉及外部平台限制，需提供替代驗證方式

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系統 MUST 在 Telegram 對話中提供語意一致的回覆
- **FR-002**: 系統 MUST 允許使用者以自然語言提出「記住某件事」的需求
- **FR-003**: 系統 MUST 在偵測到記憶需求時建立當日記憶檔案並寫入內容
- **FR-004**: 記憶檔案 MUST 儲存在 `/data/data/com.termux/files/home/storage/shared/C_Dong_bot`
- **FR-005**: 記憶檔案 MUST 以 `YYYY-MM-DD.md` 為檔名
- **FR-006**: 系統 MUST 允許使用者以自然語言要求回顧或查詢已記住的內容
- **FR-007**: 系統 MUST 在回覆前形成「目標 → 行動 → 觀察」的迭代計畫，且在使用者要求時可簡述其規劃與觀察
- **FR-008**: 系統 MUST 在必要時主動提出澄清問題以完成目標
- **FR-009**: 當使用者以不同說法提出相同目的時，系統 MUST 能給出一致的回覆
- **FR-010**: 記憶內容 MUST 保持原意且可讀
- **FR-011**: 系統 MUST 偵測目標導向迭代中的重複迴圈，並在無進展時自動停止以避免長時間無回覆
- **FR-012**: 系統 MUST 在自動停止時回覆使用者簡短說明並建議下一步

*Example of marking unclear requirements:*

- **FR-013**: 系統 MUST 僅支援私聊（單一使用者）對話
- **FR-014**: 記憶查詢範圍 MUST 預設為當日，並允許使用者指定日期或日期區間
- **FR-015**: 記憶觸發的判定方式 MUST 以語意自主判斷為主

### Key Entities *(include if feature involves data)*

- **記憶條目**: 使用者要求記住的內容與其上下文
- **記憶檔案**: 以日期命名的每日記憶集合
- **對話目標**: 使用者在對話中希望完成的目的
- **行動計畫**: 為達成對話目標所產生的步驟集合

## Assumptions

- 主要使用者為單一管理者，且擁有對記憶資料的讀寫權限
- 使用者可接受機器人以自然語言回覆，不需固定格式
- 範圍不包含管理後台、金流、或多平台同步

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 90% 以上的對話需求可在 2 輪對話內完成主要目標
- **SC-002**: 使用者輸入記憶需求後，DongDong 於 5 秒內回覆確認
- **SC-003**: 記憶查詢的回覆命中率達 95% 以上（以人工抽測判定）
- **SC-004**: 使用者對回覆滿意度達 4/5 以上（以簡易回饋統計）
- **SC-005**: 當迭代重複且無進展時，系統在自適應上限內停止並回覆說明
