# Phase 0 Research: 網路搜尋彙整

## Decision 1: 搜尋模型選擇

- **Decision**: 使用 gpt-4o-mini-search-preview 作為搜尋與摘要模型。
- **Rationale**: 該模型提供搜尋能力並可直接產出摘要，符合即時彙整需求。
- **Alternatives considered**: 一般對話模型 + 外部搜尋服務（整合成本較高）。

## Decision 2: 摘要回覆格式

- **Decision**: 統一輸出「摘要 / 重點 / 來源」三段格式。
- **Rationale**: 一致格式便於閱讀與比對，也符合規格中的回覆一致性要求。
- **Alternatives considered**: 僅摘要或僅列來源（資訊密度不足）。

## Decision 3: 連結摘要處理

- **Decision**: 由搜尋模型處理連結內容並產出摘要。
- **Rationale**: 簡化系統流程，避免額外網頁抓取與解析流程。
- **Alternatives considered**: 自行擷取網頁內容再交由模型摘要（較複雜）。
