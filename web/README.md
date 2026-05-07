# `web/` ── HTTP 應用層

這個資料夾**取代了原 `my_stock_bot` 的 `discord_bot/`**。把原本「Discord 指令」改成「HTTP API + 排程」。

> 🚪 入口在 `app.py`（在 repo 根目錄），它會 import 這裡的 `handlers` 和 `scheduler`。

## 檔案功能對照

| 檔案 | 功能 |
|---|---|
| `__init__.py` | 套件初始化 |
| `handlers.py` | **HTTP 路由**：`/api/run`、`/api/buy`、`/api/sell`、`/api/holding`、`/api/challenge`、`/api/stock`、`/api/report` 等等 |
| `scheduler.py` | **排程器**：週一~五 17:00 跑 `analysis.py` + 撮合；週五 18:00 / 21:00 結算 |
| `settle.py` | 週五結算（1 週 + 2 週）；無 Discord 推播 |
| `portfolio.py` | 持倉操作（買、賣、查持倉、損益排行榜） |
| `challenge.py` | 選股挑戰（加入 / 結算 / 排行） |
| `stats_view.py` | 統計檢視（勝率、各等級表現、報表） |
| `auth.py` | 寫入操作的 HTTP Basic Auth（`WEB_PASSWORD`） |
| `state.py` | 執行緒安全的共用狀態（目前只放 `LAST_RUN`） |

## API 端點對照

完整列表見 [`README.md` § API 端點](../README.md#api-端點)。簡略：

```
GET  /api/stock?sid=2330       個股查詢（CORS 開放、不需密碼）
GET  /api/topbuyer             外資買超 Top 10
GET  /api/topseller            外資賣超 Top 10
GET  /api/holding              目前持倉
GET  /api/challenges           本週挑戰
GET  /api/last_run             最近一次分析狀態
GET  /api/report  /api/stats   報表 / 詳細統計

POST /api/run                  手動觸發盤後分析
POST /api/buy                  {"sid","price","shares"}
POST /api/sell                 {"sid","price","shares"}
POST /api/challenge            {"sid"} 加入本週挑戰
POST /api/challenge/settle     手動結算本週挑戰
```

> POST 端點若有設 `WEB_PASSWORD` 環境變數，需要 HTTP Basic Auth。
> 使用者名稱可隨便填，密碼填 `WEB_PASSWORD` 的值。

## 排程時間（台灣時區）

| 時間 | 動作 |
|---|---|
| 週一~五 17:00 | 盤後篩選 + 昨日 T+1 撮合 + Dashboard 同步 |
| 週五 18:00 | 1 週 + 2 週結算（含 missed 假設結算） |
| 週五 21:00 | 選股挑戰結算 + 清空當週 |
| 服務啟動時 | 自動 export Dashboard 一次（內容無變動 → 跳過 push） |

> 17:00 失敗 **不自動重試**；手動到 admin.html 按「🚀 觸發盤後分析」即可，
> 或從 Dashboard 右上角的「🚀 立即跑」直接觸發。
