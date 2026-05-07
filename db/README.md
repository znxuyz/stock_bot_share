# `db/` ── 資料庫層（PostgreSQL）

這個資料夾包住所有跟 PostgreSQL 互動的程式。**外面的程式只 import 這裡，不直接寫 SQL**。

> 🔌 連線資訊從 `DATABASE_URL` 環境變數來（Railway 加 PostgreSQL plugin 時會自動注入）。

## 檔案功能對照

| 檔案 | 功能 |
|---|---|
| `__init__.py` | Schema 版本 / 套件初始化 |
| `conn.py` | psycopg2 連線池 + `with get_conn()` context manager |
| `schema.py` | 建表 / 升級 schema（v5-web）；服務啟動時會自動跑 |
| `runs.py` | 每次盤後分析的執行紀錄（成功 / 失敗 / 耗時） |
| `screens.py` | 篩選結果（SS / S / A / CHASE / WATCH 各檔的進場價、目標、停損） |
| `settle.py` | T+1 撮合結果、1 週 / 2 週結算結果 |
| `stats.py` | 累積勝率、各等級表現、月份報表計算 |
| `holdings.py` | 持倉（買進、賣出、FIFO 損益計算） |
| `challenges.py` | 「本週選股挑戰」加入 / 結算 |

## Schema 版本

- 目前是 **v5-web**（單人版）
- 從 v4 以前升上來時 **會自動清空 `screen_records`**（因為欄位不相容）
- 升 schema 不會弄丟 `holdings` / `challenges` 資料

## 常見問題

**Q：手動清空所有資料怎麼做？**
Railway → Postgres plugin → Settings → Danger Zone → **Reset Database**。
服務重啟後會自動重建空 schema。

**Q：為什麼分這麼多檔案？**
按「業務領域」分（執行紀錄 / 篩選 / 結算 / 統計 / 持倉 / 挑戰），
比一個 `db.py` 塞 800 行好讀也好測。
