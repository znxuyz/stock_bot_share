# 新手操作說明（給第一次用的人）

這份說明分兩塊：**A. 部署（一次性）** 給會用 GitHub / Railway 的人看一次就好；
**B. 日常使用** 給爸爸（或任何不懂程式的使用者）看，照著按按鈕就能用。

---

## A. 部署（只做一次，給技術人員）

### A-1. 開 Railway 服務

1. 到 [railway.app](https://railway.app/) 用 GitHub 帳號登入
2. **New Project → Deploy from GitHub repo**，選 `znxuyz/stock_bot_share`
3. 進入 service → **Settings → Networking → Generate Domain**，會得到一個網址，例如
   `https://stockbotshare-production.up.railway.app`，先抄起來
4. 點 **+ New → Database → Add PostgreSQL**，Railway 會自動把 `DATABASE_URL` 注入到主 service

### A-2. 申請 GitHub Personal Access Token

讓後端可以把每日資料 push 回 `docs/data/*.json`。

1. GitHub 右上角頭像 → **Settings → Developer settings → Personal access tokens → Fine-grained tokens**
2. **Generate new token**：
   - Token name：`stock_bot_share`
   - Expiration：90 days（之後快到期會 email 提醒，再回來重新產生）
   - Repository access：**Only select repositories** → 選 `stock_bot_share`
   - Permissions → Repository permissions → **Contents：Read and write**
3. 按 **Generate token**，複製出現的 `github_pat_...` 字串（只會顯示一次）

### A-3. 在 Railway 設定環境變數

回到 Railway service → **Variables** 頁，逐項加入：

| 變數 | 值 |
|------|-----|
| `GITHUB_TOKEN`   | 上一步剛複製的 `github_pat_...` |
| `BOT_PUBLIC_URL` | A-1 抄下來的 Railway 網址 |
| `WEB_PASSWORD`   | （選填）任意密碼，會用來保護「執行 / 買 / 賣」等操作；留空 = 任何人都能操作（風險：URL 外流即可寫入）|
| `USER_NAME`      | （選填）持倉顯示的名字，例如 `爸爸` |

`DATABASE_URL` Railway 自動注入，**不用自己填**。

按 **Deploy** 等 1~2 分鐘，狀態變成綠色 Active 就完成了。

### A-4. 開 GitHub Pages

到 `znxuyz/stock_bot_share` repo 的 **Settings → Pages**：
- Source：`Deploy from a branch`
- Branch：選 `main`、資料夾選 `/docs`、按 **Save**
- 等 1~2 分鐘，Pages 就會發布到
  `https://znxuyz.github.io/stock_bot_share/`

### A-5. 第一天先手動跑一次（可選）

打開 `https://znxuyz.github.io/stock_bot_share/admin.html`，
- **服務位址** 填 A-1 的 Railway 網址，按「儲存」
- 在「🚀 觸發盤後分析」按「執行」
- 等 3~5 分鐘，Dashboard 會自動更新出當日結果

之後每個交易日下午 5 點服務會自己跑，不需要再手動。

---

## B. 日常使用（給爸爸）

### B-1. 兩個網址記起來

| 用途 | 網址 |
|------|------|
| 看當日篩選 / 統計 | https://znxuyz.github.io/stock_bot_share/ |
| 買賣 / 操作 | https://znxuyz.github.io/stock_bot_share/admin.html |

建議手機把這兩個加到首頁書籤。

### B-2. 第一次開 admin.html 要做的事

1. 打開 https://znxuyz.github.io/stock_bot_share/admin.html
2. 最上面「📡 服務位址」那一格，填入兒子告訴你的 Railway 網址
   （形如 `https://stockbotshare-production.up.railway.app`），按「儲存」
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

### B-7. 常見狀況

**Q：今天打開 Dashboard 沒有更新？**
A：交易日下午 5:00 服務才會跑，5:30 之後再看。如果隔天還是沒變，到 admin.html 按「🚀 觸發盤後分析」手動跑一次。

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

## 風險聲明

本系統僅供研究與教育用途，**不構成投資建議**。
策略勝率為歷史模擬，不保證未來表現；任何下單都應自行判斷風險。
