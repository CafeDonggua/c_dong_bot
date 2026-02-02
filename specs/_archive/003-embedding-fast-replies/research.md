# Phase 0 Research: 內嵌檢索與快速回覆

## Decision 1: Telegram 更新機制選擇

- **Decision**: 維持既有 long polling（getUpdates）為預設；若部署環境允許且需要更穩定的即時性，再切換為 webhook。
- **Rationale**: Telegram Bot API 支援 long polling 與 webhook 兩種模式，對個人助理場景而言，long polling 部署成本低、適合本地或自架環境；回覆延遲更受應用端流程與模型耗時影響。
- **Alternatives considered**: 直接改為 webhook（需要公開可被 Telegram 連線的 HTTPS 端點與穩定部署）。

## Decision 2: 向量檢索的相似度量與模型

- **Decision**: 使用 text-embedding-3-small 產生向量，採用 cosine similarity 作為相似度度量。
- **Rationale**: OpenAI embeddings 指引使用向量相似度（常見為 cosine similarity）進行檢索；text-embedding-3-small 為輕量模型，適合個人助理場景與成本控制。
- **Alternatives considered**: 使用較大型 embedding 模型（成本更高、延遲更高）。

## Decision 3: 本地 RAG 取捨

- **Decision**: 以「本地可得記憶」優先檢索；採用本地持久化的向量索引（小量資料即可支撐），避免外部向量服務。
- **Rationale**: 個人助理資料量小且以私聊/小群為主，本地索引可降低網路往返與外部依賴，符合效能目標與「必要時才使用工具」的原則。
- **Alternatives considered**: 外部向量資料庫（可擴充但增加成本與部署複雜度）。
