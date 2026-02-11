# Release Policy

本文件定義穩定版與預覽版的發布規則，目標是讓使用者明確知道 `1.0.x` 才是穩定通道。

## 分支策略

- `main`: 穩定通道，只接受可正式發布的內容。
- `next`: 預覽通道，整合下一版功能（beta/rc）。
- `feature/*` 或 `001-*`: 功能開發分支，合併到 `next`。

## 版本號策略

- 穩定版（main）使用正式語意版本：
  - `1.0.0`, `1.0.1`, `1.1.0`
- 預覽版（next）使用預發布標記：
  - `1.1.0-beta.1`
  - `1.1.0-rc.1`

## GitHub Release 策略

- 正式版：
  - Tag 形式：`v1.0.0`
  - Branch：`main`
  - Release 型態：`Latest`（不要勾 `Pre-release`）
- 預覽版：
  - Tag 形式：`v1.1.0-beta.1` / `v1.1.0-rc.1`
  - Branch：`next`
  - Release 型態：必須勾 `Pre-release`

## 對外下載指引

- README 只主推穩定版 tag（例如 `v1.0.0`）。
- 預覽版只放在「預覽通道」段落，並標示「測試用途」。

## 發版流程

1. 功能分支合併到 `next`。
2. 在 `next` 建立預覽 tag（beta/rc），發布為 `Pre-release`。
3. 驗證完成後，將版本內容合併到 `main`。
4. 在 `main` 建立正式 tag，發布為正式版。

## 快速檢查

可在發版前執行：

```bash
sh scripts/release_gate.sh <branch> <version>
```

範例：

```bash
sh scripts/release_gate.sh main 1.0.0
sh scripts/release_gate.sh next 1.1.0-beta.1
```
