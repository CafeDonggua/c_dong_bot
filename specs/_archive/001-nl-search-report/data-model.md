# Data Model: 自然語言搜尋與案例整理

## Entities

### 自然語言請求 (NLRequest)
- **欄位**: request_id, user_id, input_text, created_at
- **關係**: 對應搜尋主題與案例文件
- **驗證**: input_text 不可為空

### 搜尋主題 (SearchTopic)
- **欄位**: request_id, summary_keywords, created_at
- **關係**: 對應 NLRequest
- **驗證**: summary_keywords 不可為空

### 案例文件 (CaseReport)
- **欄位**: report_id, request_id, title, file_path, created_at
- **關係**: 對應 NLRequest
- **驗證**: file_path 必須存在且可存取

### 記憶紀錄 (MemoryLog)
- **欄位**: date, entries (text, link)
- **關係**: 對應 CaseReport
- **驗證**: link 必須指向案例文件

## Relationships

- NLRequest 1:1 SearchTopic
- NLRequest 1:1 CaseReport
- CaseReport 1:N MemoryLog
