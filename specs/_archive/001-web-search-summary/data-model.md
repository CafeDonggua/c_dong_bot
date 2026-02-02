# Data Model: 網路搜尋彙整

## Entities

### 搜尋請求 (SearchRequest)
- **欄位**: request_id, user_id, input_type (keyword | url), query_text, created_at
- **關係**: 對應搜尋結果與摘要輸出
- **驗證**: query_text 需非空；input_type 必須為允許集合之一

### 搜尋結果 (SearchResult)
- **欄位**: request_id, sources (url, title), raw_summary, created_at
- **關係**: 對應 SearchRequest
- **驗證**: sources 至少 1 筆

### 摘要輸出 (SummaryOutput)
- **欄位**: request_id, summary, bullet_points, sources, created_at
- **關係**: 對應 SearchRequest
- **驗證**: summary 與 sources 必須存在

## Relationships

- SearchRequest 1:1 SearchResult
- SearchRequest 1:1 SummaryOutput
