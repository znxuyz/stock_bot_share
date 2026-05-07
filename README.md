# 川投顧量化系統 ── 純網頁版（單人）

> # 🚀 第一次安裝看這裡 → **[`SETUP_GUIDE.md`](SETUP_GUIDE.md)**
>
> 從 fork、Railway 部署、GitHub Pages、Token 申請到日常使用，**完整逐步圖文教學在 `SETUP_GUIDE.md`**，遇到任何問題先查這份。

| 你想做什麼 | 看這裡 |
|---|---|
| 🆕 第一次部署 / 不知道從哪開始 | [`SETUP_GUIDE.md` § A 部署](SETUP_GUIDE.md#a-部署一次性) |
| 📱 已經部署好，想學日常怎麼用 | [`SETUP_GUIDE.md` § B 日常使用](SETUP_GUIDE.md#b-日常使用) |
| 🔧 部署遇到問題（Railway crash / 403 / 空白） | [`SETUP_GUIDE.md` § A-7 部署常見問題](SETUP_GUIDE.md#a-7-部署常見問題) |
| 📂 不知道某個資料夾 / 檔案是做什麼的 | 本檔案下方 [模組結構](#模組結構) |

---

`my_stock_bot` 拿掉 Discord 推播後的純網頁版本。每個交易日盤後 17:00 自動抓
TWSE 法人 / 量價資料、跑同一套 4 層篩選漏斗，把結果寫進 GitHub Pages dashboard；
買賣紀錄、選股挑戰、手動觸發分析等操作改在 `docs/admin.html` 上完成。

> **適用對象**：任何 GitHub 用戶都可以 fork 此 repo 自行部署，**不需修改任何 hardcoded 字串**。

| 服務 | 連結 |
|------|------|
| 後端 HTTP（Railway） | `https://<your-railway-url>` |
| Dashboard | `https://<USERNAME>.github.io/<REPO>/` |
| 操作面板 | `https://<USERNAME>.github.io/<REPO>/admin.html` |
| 個股 API | `https://<your-railway-url>/api/stock?sid=2330` |

> 上述 `<USERNAME>` 是你的 GitHub 帳號、`<REPO>` 是你 fork 後的 repo 名稱。

策略邏輯與 [`my_stock_bot`](https://github.com/znxuyz/my_stock_bot) 完全相同
（同一份 `analysis.py / scoring.py / chase.py / entry_zone.py / matching.py / db/...`），
本 repo 只處理「網頁化」與「單人化」。

---

## 與 my_stock_bot 的差異

| | my_stock_bot | 本 repo |
|--|--|--|
| 觸發 / 操作 | Discord 指令 | 網頁表單（`docs/admin.html`） |
| 推播 | Discord webhook | 不推播；結果只在 dashboard 顯示 |
| 多伺服器 | guild_settings / 每個 guild 一份資料 | 單人版固定 `guild_id='default'` |
| 額外指令 | `/fortune /roast /poll /leaderboard` | 不提供 |
| Schema | v4-macd-chase | v5-web（首次部署會自動清空 `screen_records`） |

策略參數（門檻、評分權重、進場區間倍率…）沿用 `config.py` 預設值，要修改直接改程式碼即可。

---

## 部署（Railway）

完整步驟見 [`SETUP_GUIDE.md`](SETUP_GUIDE.md) 的 A 部分。簡略：

1. **Fork 此 repo** 到你自己的 GitHub 帳號（取個你想要的 repo 名稱）
2. **新建 Railway 專案** → Connect to 你 fork 的 repo
3. **加 PostgreSQL plugin**（Railway 自動注入 `DATABASE_URL`）
4. **設定環境變數**：

   | 變數 | 必填 | 說明 |
   |------|------|------|
   | `DATABASE_URL`   | ✅（Railway 自動注入） | PostgreSQL |
   | `GITHUB_TOKEN`   | ✅ | Fine-grained PAT，**Contents: Read and write** |
   | `GITHUB_REPO`    | ✅ | 你 fork 的 repo，格式 `<USERNAME>/<REPO>` |
   | `GITHUB_BRANCH`  | ⚪ | 預設 `main` |
   | `BOT_PUBLIC_URL` | ✅ | 部署後的 Railway 公開 URL（給 dashboard 個股查詢用） |
   | `WEB_PASSWORD`   | ⚪ | admin 寫入操作密碼；留空 = 不驗證 |
   | `USER_NAME`      | ⚪ | 持倉顯示用名稱 |
   | `LOG_LEVEL`      | ⚪ | `INFO`（預設） |

5. **啟用 GitHub Pages**：repo Settings → Pages → Source = Deploy from branch (`main`, `/docs`)

部署完成後，dashboard 自動同步 `docs/data/*.json`；admin 頁第一次開啟要在「服務位址」
欄位填入 Railway URL，按儲存。

---

## 篩選策略（沿用 my_stock_bot 完整漏斗）

| | 條件 |
|---|---|
| 第 1 輪 | 收盤 ≥ 10 元、漲幅 ≥ 1%、法人雙買超 OR 單方買超 ≥ 100K 股 |
| 第 2 輪 | 候選 > 30 檔時依「外資+投信合計」截 30 名 |
| 第 3 輪 | 量比 ≥ 1.5x、EMA 多頭排列 20>60>120（或備援 10>20>60） |
| 第 4 輪 | 8 項評分（總分 105）+ 籌碼 / 大盤 / 融資加減項；門檻 SS≥85、S≥68、A≥52 |

連續 ≥ 3 日漲停會走「強勢追漲」特殊路徑（5 項追漲門檻；5/5 → CHASE，4/5 → WATCH）。
進場與結算邏輯（v5）：T+1 撮合、目標 +5%/+10%、停損 -5%、第 1/2 個週五結算。

詳細策略說明見 [`my_stock_bot/PROJECT_STATUS.md`](https://github.com/znxuyz/my_stock_bot/blob/main/PROJECT_STATUS.md)。

---

## 模組結構

> 💡 **每個資料夾都有自己的 README.md**，點進去可看更詳細的檔案說明。

### 頂層檔案

| 檔案 | 角色 | 說明 |
|---|---|---|
| `SETUP_GUIDE.md` | 📖 **必讀** | 完整安裝與日常使用教學 |
| `README.md` | 📖 | 本檔案，總覽 + 模組地圖 |
| `requirements.txt` | ⚙️ | Python 依賴（`pip install -r` 用） |
| `app.py` | 🚀 進入點 | HTTP server + 啟動排程器 |
| `config.py` | ⚙️ 設定 | 環境變數讀取、策略門檻常數 |
| `analysis.py` | 🧠 主流程 | 盤後 4 層篩選漏斗（取代 Discord 版） |
| `stock_analyzer.py` | 🔍 個股 | `/api/stock` 用的單檔分析 |
| `web_export.py` | 📤 推送 | 把 DB 結果寫成 JSON 並 push 到 `docs/data/` |
| `matching.py` | 📊 撮合 | T+1 開盤撮合、進場價判定 |
| `scoring.py` | 🧮 評分 | 8 項評分 + 加減項，總分 105 |
| `chase.py` | 🚀 追漲 | 連 ≥ 3 日漲停的特殊路徑 |
| `entry_zone.py` | 🎯 進場區 | 隔日合理進場區間計算 |
| `topflow.py` | 💰 籌碼 | 外資 / 投信 Top 買賣超 |
| `indicators.py` | 📈 指標 | EMA / 量比 / RSI / MACD 等 |
| `advanced_indicators.py` | 📈 進階指標 | 乖離、KD、布林、BBI 等 |
| `twse_http.py` | 🌐 TWSE | HTTP 抓取 + 限速退避 |
| `twse_kbar.py` | 🌐 TWSE | K 棒歷史 |
| `twse_t86.py` | 🌐 TWSE | 三大法人買賣超（T86） |
| `twse_market.py` | 🌐 TWSE | 大盤資訊（MI_INDEX） |
| `twse_margin.py` | 🌐 TWSE | 融資融券 |
| `time_utils.py` | 🕐 工具 | 台北時區、交易日判斷 |
| `format_utils.py` | 🛠️ 工具 | 格式化（百分比、千分位…） |
| `logging_setup.py` | 📝 工具 | 統一 logger 設定 |

### 資料夾

| 資料夾 | 用途 | 詳細 |
|---|---|---|
| [`db/`](db/) | 🗄️ **資料庫層**（PostgreSQL） | 連線、schema、各種讀寫（持倉 / 篩選 / 結算 / 統計 / 挑戰） |
| [`web/`](web/) | 🌐 **HTTP 應用層**（取代原 Discord bot） | 路由、排程、auth、買賣 / 挑戰 / 統計 view |
| [`docs/`](docs/) | 📊 **GitHub Pages 前端** | Dashboard `index.html` + 操作面板 `admin.html` + JSON 資料 |
| [`tests/`](tests/) | 🧪 **單元測試** | pytest 純邏輯測試（不打 TWSE / DB） |
| `.github/` | 🤖 GitHub 設定 | workflows（CI） |

### 一張圖看資料怎麼流動

```
                17:00 排程
                    │
                    ▼
   ┌────────────────────────────────────┐
   │  web/scheduler.py 觸發              │
   │      └─→ analysis.py 跑 4 層篩選     │
   │              ├─→ twse_*.py 抓資料    │
   │              ├─→ indicators.py 算   │
   │              ├─→ scoring.py 評分    │
   │              └─→ db/screens.py 寫入 │
   └─────────────┬──────────────────────┘
                 │
                 ▼
   ┌────────────────────────────────────┐
   │  web_export.py                      │
   │      ├─→ docs/data/*.json（本機）    │
   │      └─→ GitHub API push（雲端）     │
   └─────────────┬──────────────────────┘
                 │
                 ▼  GitHub Pages 自動 redeploy
   ┌────────────────────────────────────┐
   │  docs/index.html  ←  使用者瀏覽器     │
   │  docs/admin.html  ←  使用者操作       │
   └────────────────────────────────────┘
```

---

## API 端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/stock?sid=2330` | 個股查詢（CORS 開放） |
| GET | `/api/topbuyer` / `/api/topseller` | 外資買 / 賣超 Top 10 |
| GET | `/api/holding` | 目前持倉 + 損益 |
| GET | `/api/challenges` | 本週挑戰列表 |
| GET | `/api/last_run` | 最後一次分析狀態 |
| GET | `/api/report` / `/api/stats` | 累積 / 詳細統計 |
| POST | `/api/run` | 手動觸發分析 |
| POST | `/api/buy` | `{"sid","price","shares"}` |
| POST | `/api/sell` | `{"sid","price","shares"}` |
| POST | `/api/challenge` | `{"sid"}` 加入本週挑戰 |
| POST | `/api/challenge/settle` | 手動結算本週挑戰 |

POST 端點若 `WEB_PASSWORD` 有設定，需要 HTTP Basic Auth（任意 user / 密碼為 `WEB_PASSWORD`）。

---

## 自動排程（台灣時間）

| 時間 | 動作 |
|------|------|
| 週一~五 17:00 | 盤後分析 + 昨日 T+1 撮合 + Dashboard 同步 |
| 週五 18:00 | 1 週 + 2 週結算（含 missed 假設結算） |
| 週五 21:00 | 選股挑戰結算 + 清空當週 |
| 服務啟動 | 自動 export Dashboard 一次（內容無變動 → 跳過 push） |

17:00 失敗不自動重試；手動到 admin 頁按「執行」即可。

---

## 本機開發

```bash
git clone https://github.com/<USERNAME>/<REPO>.git
cd <REPO>
pip install -r requirements.txt
pip install pytest pyflakes

python -m pytest tests/ -v
python -m pyflakes *.py db/*.py web/*.py tests/*.py
```

---

## 授權 / 免責

僅供研究與教育用途，**不構成投資建議**。策略勝率為歷史模擬，不保證未來表現。
