# 技能品質檢核清單

用於檢核每個技能是否完整、一致且可被理解。

## 基本完整性

- 技能目錄包含 `SKILL.md`
- `SKILL.md` 含 YAML frontmatter（name/description/version）
- 必填章節完整：Summary、Triggers、Inputs、Outputs、Steps、Constraints、Safety、Examples

## 一致性與可讀性

- `name` 與目錄名稱對應且唯一
- Summary 為一句話清楚描述用途
- Triggers 能對應使用者意圖
- Steps 可依序執行且無矛盾
- Examples 至少包含 1 個正例與 1 個反例

## 安全與限制

- Constraints 明確描述不可處理的情境
- Safety 提醒敏感資料或風險

## 變更紀錄

- 有更新時同步補充 CHANGELOG.md
