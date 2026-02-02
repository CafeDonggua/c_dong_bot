# Research: Bot 監控提示訊息

**Date**: 2026-02-02
**Feature**: /storage/emulated/0/program/python/tg_bot/c_dong_bot/specs/002-bot-status-logs/spec.md

## Decision 1: 監控事件集合

**Decision**: 使用五種事件類型：啟動成功、收到訊息、回覆完成、錯誤、心跳。

**Rationale**: 與需求完全對應，且可用最少事件覆蓋「正常運行」與「異常」兩大狀態。

**Alternatives considered**:
- 只記錄啟動/錯誤：無法確認訊息處理流程。
- 只記錄心跳：無法確認錯誤與訊息處理。

## Decision 2: 錯誤重複輸出節流策略

**Decision**: 對相同錯誤摘要（以摘要字串為鍵）在 60 秒內僅輸出一次，並在下一次輸出時附上被抑制次數。

**Rationale**: 60 秒可避免短時間大量重複輸出，同時保留錯誤發生的可見性；附帶抑制次數可維持資訊密度。

**Alternatives considered**:
- 完全不節流：在錯誤迴圈時會淹沒輸出。
- 長時間節流（例如 10 分鐘）：可能延遲發現持續錯誤的狀態變化。
