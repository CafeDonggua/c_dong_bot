# Phase 0 Research: 自然語言搜尋與案例整理

## Decision 1: 自然語言意圖解析流程

- **Decision**: 先將使用者自然語言需求摘要為「搜尋主題」再執行搜尋與彙整。
- **Rationale**: 可降低搜尋噪音並提高結果相關性。
- **Alternatives considered**: 直接用原始輸入搜尋（易產生過度發散結果）。

## Decision 2: 案例文件格式

- **Decision**: 以 Markdown 檔案保存案例，包含摘要、重點、來源與結論。
- **Rationale**: 易於閱讀與長期保存。
- **Alternatives considered**: PDF 或純文字（可讀性較差或不易編輯）。

## Decision 3: 記憶與案例分流保存

- **Decision**: 記憶資料存於 memory 子資料夾，案例文件存於 reports 子資料夾，並在當日記憶檔案加入案例連結。
- **Rationale**: 分離資料類型，避免混雜。
- **Alternatives considered**: 全部存於單一目錄（不易管理）。
