# 完整安裝與使用說明

本說明分兩部分：
- **A. 部署（給技術人員，做一次）** — 從 0 開始把系統架起來
- **B. 日常使用（給最終使用者）** — 不需要懂程式

> **適用對象**：任何 GitHub 用戶都可以 fork 此 repo 自行部署，不需修改任何 hardcoded 字串。
> 以下用 `<USERNAME>` 表示你的 GitHub 帳號、`<REPO>` 表示你 fork 後的 repo 名稱。
> 例如你 fork 過去叫 `lucky/stock-bot`，那 `<USERNAME>=lucky`、`<REPO>=stock-bot`。

---

## A. 部署（一次性）

### A-0. 預先準備

需要兩個免費帳號：

| 服務 | 註冊網址 | 用途 |
|------|--------|------|
| GitHub | https://github.com/signup | 放程式碼 + 跑 Dashboard 網頁 |
| Railway | https://railway.app/login（用 GitHub 登入即可） | 跑後端服務 + 資料庫 |

> 💰 **費用提醒**：
> - **GitHub / GitHub Pages：完全免費**
> - **Railway**：新帳號送 $5 免費額度 / 月，本服務 24 小時掛網約耗 $3-5/月，**剛開始用免費額度可撐 1~2 個月**；之後若不綁信用卡服務會被暫停（免費期間到期信會通知）

### A-1. Fork 此專案到你自己的 GitHub

1. 到上游 repo 頁面 → 右上角按 **Fork** 按鈕
2. 選你的帳號當 **Owner**
3. 「Repository name」可以重新取名（不取就跟原本同名）
4. **取消勾選**「Copy the main branch only」（建議勾，但勾不勾都可以）
5. 按 **Create fork**，等 5 秒鐘 fork 完成

完成後你會在 `https://github.com/<USERNAME>/<REPO>` 看到自己的副本。

> 💡 「Fork」就是把別人的 repo 複製一份到你自己帳號下。**之後我（上游）有更新時，你可以一鍵 sync fork 拉過來**。

### A-2. 開 Railway 專案 + 加 PostgreSQL

#### A-2-1. 部署主服務
1. 到 https://railway.app/ 用 GitHub 登入
2. 首頁右上角 **New Project**
3. 選 **Deploy from GitHub repo**
4. 第一次用要授權 Railway 存取你的 GitHub repos：
   - 跳出視窗 → **Configure GitHub App**
   - 選 **Only select repositories** → 勾選 `<REPO>`
   - 按 **Install & Authorize**
5. 回 Railway，選你剛 fork 的 `<REPO>`
6. Railway 會自動偵測到 Python 並開始部署（**這次部署會失敗很正常**，因為還沒設環境變數，先別緊張）

#### A-2-2. 加 PostgreSQL 資料庫
1. 在 Railway 專案頁面，**+ Create** 或 **+ New** 按鈕
2. 選 **Database → Add PostgreSQL**
3. 等 30 秒，Postgres 起來後，會自動把 `DATABASE_URL` 注入到主服務（這步是 Railway 自動的，**你不用自己貼**）

#### A-2-3. 拿到主服務的對外網址
1. 點主服務（不是 Postgres 那塊）
2. 上方 **Settings** 頁
3. 往下滾到 **Networking** → 按 **Generate Domain**
4. 會跳出一個網址，例如 `https://stockbot-production-abcd.up.railway.app`
5. **把這個網址抄下來**，A-4 會用到

### A-3. 申請 GitHub Personal Access Token

讓 Railway 後端可以把每天篩選結果 push 回 `docs/data/*.json`，這樣 GitHub Pages dashboard 才會更新。

1. GitHub 右上角頭像 → **Settings**
2. 左邊側欄最下面 → **Developer settings**
3. 左邊 → **Personal access tokens** → **Fine-grained tokens**
4. 右上角 **Generate new token**
5. 填寫：
   - **Token name**：任意，例如 `stock-bot`
   - **Expiration**：選 90 days（之後到期前 GitHub 會 email 提醒）
   - **Resource owner**：選你自己（`<USERNAME>`）
   - **Repository access**：選 **Only select repositories** → 勾選你的 `<REPO>`
   - **Permissions** → 點開 **Repository permissions** → 找 **Contents** → 改成 **Read and write**
     ⚠️ **這一步是最常踩的雷**：必須是 `Read and write`，停在 `Read-only` 後端就會 403 推不上來
6. 拉到最下面按 **Generate token**
7. 跳出來的 `github_pat_xxxxxxxxxxxxxxxx` **馬上複製**（重新整理頁面就再也看不到，要重發）

> 🔁 **Token 90 天後到期怎麼辦？**
> 到期前一週 GitHub 會 email 提醒。回到同個頁面找原本那個 token → **Regenerate**（沿用舊權限） → 複製新 token → Railway → Variables → 換掉 `GITHUB_TOKEN` 的值即可。整個過程約 2 分鐘。

### A-4. 在 Railway 設定環境變數

回到 Railway → 點主服務 → 上方 **Variables** 頁 → **+ New Variable**，**逐項加入**：

| 變數名 | 必填 | 值 |
|------|------|-----|
| `GITHUB_TOKEN`   | ✅ | A-3 剛複製的 `github_pat_...` |
| `GITHUB_REPO`    | ✅ | `<USERNAME>/<REPO>`（例如 `lucky/stock-bot`） |
| `BOT_PUBLIC_URL` | ✅ | A-2-3 抄下來的 Railway 網址（含 `https://`） |
| `WEB_PASSWORD`   | ⚪ | 任意密碼，會用來保護「執行 / 買 / 賣」等寫入操作；留空 = 任何人知道 URL 都能操作（風險：URL 外流即可寫入） |
| `USER_NAME`      | ⚪ | 持倉顯示用名稱，預設「爸爸」 |

> 💡 **不需要自己填的**：
> - `DATABASE_URL`（Railway 自動注入）
> - `GITHUB_BRANCH`（預設 `main`，除非你 fork 後改了主分支）
> - `PORT`（Railway 自動指定）

填完所有變數後，Railway 會自動觸發新一次部署（約 1-2 分鐘），右上角狀態變成綠色 **Active** 就成功了。

#### 確認服務有起來
- 用瀏覽器打開 A-2-3 抄下的 Railway 網址
- 應該看到一行純文字 `OK - stock-bot`
- 看到了 = 後端正常運作

### A-5. 啟用 GitHub Pages（讓 Dashboard 網頁可以上線）

到你 fork 的 repo `https://github.com/<USERNAME>/<REPO>`：
1. 上方 **Settings** 標籤（不是 Railway 的）
2. 左邊側欄 → **Pages**
3. **Source** 區塊 → **Deploy from a branch**
4. **Branch** 下拉 → 選 `main`、資料夾選 `/docs`、按 **Save**
5. 等 1~2 分鐘，最上方會出現綠色提示「Your site is live at `https://<USERNAME>.github.io/<REPO>/`」

把這個網址記起來，**這就是 Dashboard 網址**。

> 🔍 第一次開可能還是空白頁面，因為 `docs/data/*.json` 都是空的（後端還沒跑過第一次篩選）。下一步會解決。

### A-6. 第一次手動跑 + 驗證一切正常

1. 打開 `https://<USERNAME>.github.io/<REPO>/admin.html`
2. **「📡 服務位址」**那一格 → 填你 A-2-3 的 Railway 網址 → 按 **儲存**
3. 「🚀 觸發盤後分析」→ 模式選 `auto` → 按 **執行**
4. 如果有設 `WEB_PASSWORD`，會跳出瀏覽器內建的密碼視窗 → 使用者名稱隨便填、密碼填 `WEB_PASSWORD` 那個值
5. **等 3~5 分鐘**

#### 如何確認跑成功？
回 Railway → 點主服務 → 上方 **Deployments** → 點當下那次 → 看 **Logs** 區。應該看到類似：
```
[執行] 模式=auto，日期=20260506
[T86] 共 19 欄
[MI_INDEX] 1234 檔
[合併] 985 檔
[過濾1] 基本條件通過：23 檔
  [1/23] 2330 ✓ 漲4.2% 量比2.8 EMA:full mode:normal
  [2/23] ...
[完成] SS=2 S=4 A=8，總耗時=240秒
[Web] ✅ 上傳 docs/data/today.json → ...
[Web] push 總結：上傳 4 / 跳過 0 / 失敗 0
```

看到 `[完成] SS=N S=N A=N` + `push 總結：上傳 4 ... 失敗 0` = 完全成功。

回 Dashboard 網址，按右上角 **🔄 重新整理**，當日篩選結果就會出現。

之後每個交易日下午 17:00 系統會自動跑，**不需要再手動**。

---

## A-7. 部署常見問題

### Q：Railway 部署一直 Crashed / Build Failed

**最常見原因**：
1. **`DATABASE_URL` 沒設**：忘記加 PostgreSQL plugin。回 A-2-2 重做。
2. **環境變數打錯**：例如 `GITHUB_REPO` 寫成了 GitHub 連結而不是 `user/repo` 格式。
3. **Token 失效**：可能 GitHub 改了權限或 token 過期。

**怎麼診斷**：
- Railway 主服務 → **Deployments** → 最新那次 → **View Logs**
- 找紅色 ERROR 或 traceback，通常會直接寫出問題

### Q：Logs 出現「Resource not accessible by personal access token」/ HTTP 403

GitHub Token **權限不足**。99% 是停在 `Contents: Read-only` 沒改 `Read and write`：

1. GitHub → Settings → Developer settings → Personal access tokens → **Fine-grained tokens**
2. 找到那個 token → **Regenerate**（或刪掉重新建）
3. **Permissions** → **Contents** 改成 `Read and write`
4. 複製新 token → Railway Variables 換掉 `GITHUB_TOKEN` 值
5. 等 redeploy 1-2 分鐘後再按一次「🚀 立即跑」

> 💡 如果你發的是 **Classic Token**（介面叫「Tokens (classic)」那一頁）也會踩到類似問題；建議改用 Fine-grained 比較穩。

### Q：Logs 寫入本機 `today.json (85 bytes)` 這麼小，是壞了嗎？

85 bytes 是空 JSON（只有 metadata，`records: []`）。代表 DB 裡還沒有篩選結果，可能原因：
1. **服務剛啟動的「空白同步」**：開機後 5 秒會自動 export 一次，這時 DB 還沒資料 → 正常
2. **手動觸發但還沒完成**：`run_analysis` 要 3-5 分鐘，期間若先 export 也是空的 → 等就好
3. **TWSE 當日無資料**：國定假日 / 颱風假 / 觸發太早（13:30 收盤後 T86 一般要等到 14:30~17:00 才上架）
4. **TWSE 限速 / 連線失敗**：見下一題

判斷方法：往上滾 logs 找有沒有這幾行：
```
[執行] 模式=auto 日期=YYYYMMDD attempt=0
[MI_INDEX] N 檔
[過濾1] 基本條件通過：N 檔
[完成] SS=N S=N A=N CHASE=N WATCH=N，總耗時=NN秒
```
都有 `[完成]` 才是真的跑完。沒看到 = 還在跑、或是中途錯誤。

### Q：Logs 出現「歷史資料不足」+「⏸ 限速退避」+「⛔ 限速中止」

TWSE 對你 Railway 服務的 IP 限速了。原因：
- 雲端 IP 容易被 TWSE 視為 bot
- Railway 同個 region 多人共用 IP，別的服務先把 quota 用光你也跟著被擋
- 你前後試了好幾次「立即跑」，每次都重抓 → 觸發限速

**解法（按推薦順序）**：
1. **等 30~60 分鐘** — TWSE 限速通常是時間性的，等就好
2. **避開尖峰時段** — 17:00~18:00 一堆服務在抓 TWSE，挑 21:00 以後比較順
3. **第二天再試** — 過了一晚通常完全恢復
4. 如果反覆失敗，編輯 `config.py`：
   ```python
   TWSE_CALL_INTERVAL_SEC = 2.5   # 拉得更慢
   RATE_LIMIT_BACKOFF_SEC = 300   # 退避 5 分鐘
   MAX_CANDIDATES         = 15    # 只抓前 15 名（少一半請求）
   ```
5. 最後一招：Railway service Settings → Networking → 換 region（如果免費方案有得選）

### Q：Dashboard 打開一片空白？

三個可能：
1. **GitHub Pages 還沒生效**（Settings → Pages 那邊有沒有顯示綠色「Your site is live at...」）→ 等 1-2 分鐘
2. **`docs/data/*.json` 還沒生成**（Railway 還沒成功 push 過任何資料）→ 看 Railway logs
3. **瀏覽器快取**（Ctrl + F5 / Cmd + Shift + R 強制重新整理）

### Q：我想砍掉重做

#### 只是想清掉 DB 資料、保留設定
- Railway → Postgres plugin → **Settings** → **Danger Zone** → **Reset Database**
- 服務重啟後會自動重建空 schema

#### 完全砍掉重做
- Railway → 主服務 → Settings → 最下面 **Delete Service**
- 砍掉 Postgres plugin 同上
- 然後從 A-2 重做即可

---

## B. 日常使用

### B-1. 兩個網址記起來

| 用途 | 網址 |
|------|------|
| 看當日篩選 / 統計 | `https://<USERNAME>.github.io/<REPO>/` |
| 買賣 / 操作 | `https://<USERNAME>.github.io/<REPO>/admin.html` |

建議手機把這兩個加到首頁書籤。

### B-2. 第一次開 admin.html 要做的事

1. 打開操作面板網址
2. 最上面「📡 服務位址」那一格，填入 Railway 網址
   （形如 `https://your-service.up.railway.app`），按「儲存」
3. 之後不用再填，瀏覽器會記住

### B-3. 每天怎麼看當日推薦

1. 下午 5:30 之後，打開 Dashboard 網址
2. 預設停在「**今日篩選**」那一頁
3. 表格會列出當日通過篩選的股票，重點欄位：

| 欄位 | 看什麼 |
|------|--------|
| **等級** | 🟣 SS = 最佳；🔵 S = 不錯；🟢 A = 普通；🔴 CHASE = 強勢追漲；🟡 WATCH = 觀察 |
| **代號 / 名稱** | 哪支股票 |
| **建議進場區** | 隔天開盤要在這個價格區間才買 |
| **目標 +5% / +10%** | 達到這個價格可分批賣出 |
| **停損 -5%** | 跌到這個價格務必出場 |
| **建議倉位** | 假設總資金 100 萬，這檔建議買多少%（例如 25% = 25 萬） |

> 📌 **重要觀念：不是每一檔都要買**。SS 級才是系統最看好的，A 級訊號比較弱。
> 一般做法：**只買 SS 級**、最多再加 1~2 檔 S 級，分散風險。

> 💡 **Dashboard 右上角有「🚀 立即跑」按鈕**：如果剛打開沒看到當日資料，按這個就能馬上手動觸發，不用切去 admin.html。

### B-4. 我買了 / 賣了，怎麼記錄？

打開 admin.html，捲到「🛒 買入」或「💸 賣出」那一格：
- 填代號（例如 `2330`）、買的價格、買的股數（1 張 = 1000 股）
- 按「買入」/「賣出」

買進去之後，按上面「💼 持倉」的「載入持倉」可以看到目前部位的：
- 成本價、現在的價格
- 未實現損益 = 還沒賣的部位現在賺多少 / 賠多少
- 已實現損益 = 賣掉的部分總共賺賠多少（FIFO 計算）

> 賣出按下去之前會問「確認賣出嗎」，按錯可以取消。

### B-5. 我想試試看一檔股票會不會賺，但又不想真的買

用「⚔️ 本週選股挑戰」：
- 輸入代號，按「加入」
- 系統會記下今天的價格，週五自動看漲幅多少
- 不用真的下單，純記分

### B-6. Dashboard 各分頁怎麼看

| 分頁 | 看什麼 |
|------|--------|
| **今日篩選** | 今天系統推薦哪些 |
| **結算狀態** | 之前推薦的股票後來怎麼樣（賺 / 賠 / 觸目標 / 觸停損） |
| **勝率統計** | 累積到現在的整體勝率，可看哪個等級表現最好 |
| **歷史紀錄** | 全部歷史推薦清單，可搜尋 / 篩日期 |

右下角藍色 **+** 按鈕點開來有 5 個小工具：

| 圖示 | 功能 |
|------|------|
| 📋 | 系統的篩選邏輯與評分規則一覽 |
| 📊 | 當日外資買 / 賣超 Top 10 |
| 🔍 | **個股查詢**：輸入任何代號（例如 2330）看分析 |
| 📚 | 每個技術指標（RSI / MACD / 乖離率…）是什麼意思 |
| ⭐ | 把感興趣的股票加入追蹤（純存在瀏覽器，不上傳） |

### B-7. 日常常見狀況

**Q：今天打開 Dashboard 沒有更新？**
A：交易日下午 5:00 服務才會跑，5:30 之後再看。如果隔天還是沒變，**直接在 Dashboard 右上角按「🚀 立即跑」就可以手動觸發**（也可以到 admin.html 按「🚀 觸發盤後分析」，效果一樣）。

**Q：今天是國定假日 / 颱風假，沒有交易？**
A：系統會自動偵測，不會發訊息，Dashboard 會保留前一個交易日的資料。

**Q：admin.html 按按鈕沒反應？**
A：檢查上面「📡 服務位址」那格有沒有填對；應該長得像 `https://xxx.up.railway.app` 沒結尾斜線。如果有設密碼（`WEB_PASSWORD`），第一次按按鈕瀏覽器會跳出視窗叫你輸入：使用者名稱隨便填，密碼填當初設定的那個。

**Q：個股查詢按鈕（🔍）說「請設定 API 網址」？**
A：FAB → 🔍 個股查詢的彈窗最下面會有設定區塊，把 Railway 網址填進去儲存即可（跟 admin 頁的「服務位址」是一樣的東西，只是分開存）。

**Q：要看上週推薦的賺賠？**
A：去「結算狀態」分頁，找對應的日期 / 代號就有 1 週 / 2 週的結算結果。週五 18:00 系統會自動結算當週到期的部位。

**Q：我想停損了，但跌幅還沒到 -5%？**
A：系統的 -5% 是建議，不是硬規定。你看了想出場就直接在 admin 頁「💸 賣出」記錄。系統的勝率統計是按程式自動結算邏輯算的，跟你個人的進出沒衝突。

---

## C. 維護

### 同步上游更新

如果上游 repo 有新 commit（例如 bug fix、新功能），到你 fork 的 repo：
1. 上方 `<> Code` 按鈕左邊那一排，會看到 **Sync fork** 下拉鈕
2. 點開 → 顯示「This branch is N commits behind」
3. 按 **Update branch**

GitHub 會自動 merge 上游的最新 main 到你的 main，Railway 偵測到自動 redeploy。

### 暫停服務（不再使用一陣子）

Railway → 主服務 → Settings → 找 **Pause Service**（保留設定，不再計費）。
之後想恢復按 **Resume Service** 即可。

### 永久停用

砍掉服務（A-7 「我想砍掉重做」最後那段）。
GitHub repo 可以保留（不會花錢），也可以直接 Delete repository。

---

## 風險聲明

本系統僅供研究與教育用途，**不構成投資建議**。
策略勝率為歷史模擬，不保證未來表現；任何下單都應自行判斷風險。
