# Dashboard 部署說明

這個資料夾是 [GitHub Pages](https://pages.github.com/) 的靜態網站來源。

## 啟用步驟（GitHub UI）

1. 進到 repo → **Settings** → **Pages**
2. **Source**：選 `Deploy from a branch`
3. **Branch**：選 `main`，資料夾選 `/docs`
4. 按 **Save**，等 1~2 分鐘後 Pages 就會發佈到
   `https://znxuyz.github.io/stock_bot_share/`

## 自動更新

服務（Railway 上的 `app.py`）每天盤後 17:00 篩選完成後會呼叫 `web_export.export_dashboard()`：
1. 從 PostgreSQL 撈出最新一日的篩選結果、歷史紀錄與彙總勝率
2. 寫成 `data/today.json`、`data/stats.json`、`data/history.json`
3. 透過 GitHub REST API（`PUT /repos/{owner}/{repo}/contents/{path}`）推回此目錄
4. GitHub Pages 會在數十秒內自動 redeploy

每週五 18:00 結算 1 週/2 週報酬後也會再推一次。

## 必要環境變數（Railway）

| 變數 | 用途 |
|------|------|
| `GITHUB_TOKEN` | Personal Access Token（fine-grained，需 `Contents: Read & Write`） |
| `GITHUB_REPO`  | 預設 `znxuyz/stock_bot_share` |
| `GITHUB_BRANCH`| 預設 `main` |

若未設定 `GITHUB_TOKEN`，服務仍會在本機寫檔，但不會推到 GitHub。

## 個股查詢 / 操作（admin.html）

`admin.html` 提供：
- 觸發盤後分析（`/api/run`）
- 買入 / 賣出 / 查持倉
- 加入選股挑戰
- 查最近一次分析狀態

需要先設定 `WEB_PASSWORD` 環境變數，admin 操作會用 HTTP Basic Auth 提示輸入。

## 本機預覽

```bash
cd docs
python -m http.server 8000
# 開 http://localhost:8000/
```
