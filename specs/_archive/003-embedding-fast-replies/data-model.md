# Data Model: 內嵌檢索與快速回覆

## Entities

### 使用者 (User)
- **欄位**: user_id, display_name, chat_ids
- **關係**: 與訊息、對話記憶關聯
- **驗證**: user_id 必須存在且可對應 Telegram 使用者

### 訊息 (Message)
- **欄位**: message_id, user_id, chat_id, content, created_at, reply_to_message_id
- **關係**: 屬於使用者；可對應回覆訊息
- **驗證**: content 需非空

### 對話記憶 (MemoryEntry)
- **欄位**: memory_id, user_id, content, created_at, source_message_id
- **關係**: 由訊息或回覆產生；可被向量索引
- **驗證**: content 需可被向量化

### 向量索引 (EmbeddingIndex)
- **欄位**: index_id, user_id, vector, memory_id, created_at
- **關係**: 對應 MemoryEntry
- **驗證**: vector 維度與模型一致

### 檢索結果 (RetrievalResult)
- **欄位**: query, matches (memory_id, score), created_at
- **關係**: 對應 MemoryEntry 與相似度分數
- **驗證**: score 需為 0~1 範圍（或模型相似度定義）

### 工具調用決策 (ToolDecision)
- **欄位**: message_id, decision (direct_reply | use_tool), reason
- **關係**: 對應 Message
- **驗證**: decision 必須為允許集合之一

## Relationships

- User 1:N Message
- User 1:N MemoryEntry
- MemoryEntry 1:1 EmbeddingIndex
- Message 1:1 ToolDecision
- RetrievalResult N:1 MemoryEntry
