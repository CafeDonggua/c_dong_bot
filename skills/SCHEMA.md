# Agent Skills 定義規範（本專案）

本文件定義本專案 `skills/` 目錄中的技能檔案格式與必要欄位，用於一致性與可驗證性。

## 目錄規範

- 每個技能一個目錄：`skills/<skill-id>/`
- 目錄內必須包含 `SKILL.md`
- 其他檔案（如 `assets/`、`references/`）視需要新增

## SKILL.md 必要結構

### YAML Frontmatter（必填）

```yaml
---
name: 技能名稱（人類可讀）
description: 一句話描述技能用途
version: 1.0.0
---
```

### 章節（必填）

- `## Summary`
- `## Triggers`
- `## Inputs`
- `## Outputs`
- `## Steps`
- `## Constraints`
- `## Safety`
- `## Examples`

## 內容規範

- `Summary`：一句話清楚說明用途
- `Triggers`：描述使用者意圖或情境
- `Inputs/Outputs`：列出必要輸入與輸出格式
- `Steps`：可依序執行的步驟
- `Constraints`：明確限制與禁用情境
- `Safety`：安全與隱私注意事項
- `Examples`：至少 1 個正例與 1 個反例

## 命名與一致性

- `skill-id` 必須唯一
- `name` 不得與其他技能重複
- 內容需保持正體中文
