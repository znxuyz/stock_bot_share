# 新手操作說明（給第一次用的人）

這份說明分兩塊：**A. 部署（一次性）** 給會用 GitHub / Railway 的人看一次就好；
**B. 日常使用** 給爸爸（或任何不懂程式的使用者）看，照著按按鈕就能用。

> 以下用 `<USERNAME>` 表示你的 GitHub 帳號、`<REPO>` 表示你 fork 後的 repo 名稱。
> 例如你 fork 過去叫 `lucky/stock-bot`，那 `<USERNAME>=lucky`、`<REPO>=stock-bot`。

---

## A. 部署（只做一次，給技術人員）

### A-0. Fork 此專案到你自己的 GitHub

1. 到上游 repo 網頁右上角按 **Fork**，選你的帳號當 owner
2. 取個喜歡的 repo 名稱（之後 `<REPO>` 就是這個）

### A-1. 開 Railway 服務

1. 到 [railway.app](https://railway.app/) 用 GitHub 帳號登入
2. **New Project → Deploy from GitHub repo**，選你 fork 的那個 repo
3. 進入 service → **Settings → Networking → Generate Domain**，會得到一個網址，例如
   `https://your-service.up.railway.app`，先抄起來
4. 點 **+ New → Database → Add PostgreSQL**，Railway 會自動把 `DATABASE_URL` 注入到主 service

### A-2. 申請 GitHub Personal Access Token

讓後端可以把每日資料 push 回 `docs/data/*.json`。

1. GitHub 右上角頭像 → **Settings → Developer settings → Personal access tokens → Fine-grained tokens**
2. **Generate new token**：
   - **Token name**：任意，例如 `stock-bot`
   - **Expiration**：90 days（之後快到期會 email 提醒，再回來重新產生）
   - **Resource owner**：選你自己（`<USERNAME>`）
   - **Repository access**：**Only select repositories** → 勾選 `<REPO>`
   - **Permissions** → **Repository permissions** → **Contents：Read and write**
     ⚠️ **必須是 Read and write，不是 Read-only**（最常踩這個雷）
3. 按 **Generate token**，複製出現的 `github_pat_...` 字串（**只會顯示一次**）

### A-3. 在 Railway 設定環境變數

回到 Railway service → **Variables** 頁，逐項加入：

| 變數 | 值 |
|------|-----|
| `GITHUB_TOKEN`   | 上一步剛複製的 `github_pat_...` |
| `GITHUB_REPO`    | `<USERNAME>/<REPO>`（例如 `lucky/stock-bot`） |
| `BOT_PUBLIC_URL` | A-1 抄下來的 Railway 網址 |
| `WEB_PASSWORD`   | （選填）任意密碼，會用來保護「執行 / 買 / 賣」等操作；留空 = 任何人都能操作（風險：URL 外流即可寫入）|
| `USER_NAME`      | （選填）持倉顯示的名字 |

`DATABASE_URL` Railway 自動注入，**不用自己填**。

按 **Deploy** 等 1~2 分鐘，狀態變成綠色 Active 就完成了。

### A-4. 開 GitHub Pages

到你 fork 的 repo 的 **Settings → Pages**：
- **Source**：`Deploy from a branch`
- **Branch**：選 `main`、資料夾選 `/docs`、按 **Save**
- 等 1~2 分鐘，Pages 就會發布到
  `https://<USERNAME>.github.io/<REPO>/`

### A-5. 第一天先手動跑一次（可選）

打開 `https://<USERNAME>.github.io/<REPO>/admin.html`：
- **服務位址** 填 A-1 的 Railway 網址，按「儲存」
- 在「🚀 觸發盤後分析」按「執行」
- 等 3~5 分鐘，Dashboard 會自動更新出當日結果

之後每個交易日下午 5 點服務會自己跑，不需要再手動。

---

## B. 日常使用（給最終使用者）

### B-1. 兩個網址記起來

| 用途 | 網址 |
|------|------|
| 看當日篩選 / 統計 | `https://<USERNAME>.github.io/<REPO>/` |
| 買賣 / 操作 | `https://<USERNAME>.github.io/<REPO>/admin.html` |

建議手機把這兩個加到首頁書籤。

### B-2. 第一次開 admin.html 要做的事

1. 打開操作面板網址
2. 最上面「📡 服務位址」那一格，填入兒子告訴你的 Railway 網址
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

### B-7. 常見狀況 / 故障排除

#### 部署相關

**Q：Railway logs 出現「Resource not accessible by personal access token」 / HTTP 403？**
A：GitHub Token **只給了讀權限沒給寫權限**。修法：
1. GitHub → Settings → Developer settings → Personal access tokens → **Fine-grained tokens**
2. 找到原本那個 token → **Regenerate**（或刪掉重新建）
3. **Resource owner** 是你的帳號
4. **Repository access** → Only select repositories → 勾選你的 repo
5. **Permissions** → Repository permissions → **Contents** 改成 **Read and write**（最常見錯就是停在 Read-only）
6. 按 Generate → 複製新 token
7. Railway → Variables → 換掉 `GITHUB_TOKEN` → 自動 redeploy
8. 等 1~2 分鐘後到 admin 頁再按一次「🚀 觸發盤後分析」

> 💡 如果你發的是 **Classic Token**（介面叫「Tokens (classic)」那一頁）也會踩到類似問題；建議改用 Fine-grained 比較穩。

**Q：Railway logs 寫入本機 `today.json (85 bytes)` 這樣很小，是壞了嗎？**
A：85 bytes 是空 JSON（只有 metadata，`records: []`）。代表 DB 裡還沒有篩選結果，可能原因：
1. **服務剛啟動的「空白同步」**：開機後 5 秒會自動 export 一次，這時 DB 還沒資料
2. **手動觸發但還沒完成**：`run_analysis` 要 3-5 分鐘，期間若先 export 也是空的
3. **TWSE 當日無資料**：國定假日 / 颱風假 / 觸發太早（13:30 收盤後 T86 一般要等到 14:30~17:00 才上架）
4. **TWSE 限速 / 連線失敗**：所有候選股都抓不到 K 棒

判斷方法：往上滾 logs 找有沒有這幾行：
```
[執行] 模式=auto 日期=YYYYMMDD attempt=0
[MI_INDEX] N 檔
[過濾1] 基本條件通過：N 檔
[完成] SS=N S=N A=N CHASE=N WATCH=N，總耗時=NN秒
```
都有 `[完成]` 才是真的跑完。沒看到代表還在跑、或是中途錯誤。

**Q：Railway service 一直 Crashed？**
A：點 service 看 Logs 找紅色錯誤訊息。最常見：
- `DATABASE_URL` 沒設（PostgreSQL plugin 沒加）
- Python 套件版本衝突（`requirements.txt` 有指定版本範圍）
- 程式語法錯誤（不太可能；本 repo CI 會擋）

**Q：Dashboard 打開一片空白？**
A：三個可能：
1. GitHub Pages 還沒生效（Settings → Pages 那邊有沒有顯示綠色勾勾）
2. `docs/data/*.json` 還沒生成（Railway 還沒成功 push 過任何資料）
3. 瀏覽器快取（Ctrl+F5 強制重新整理）

#### 日常使用

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

## 風險聲明

本系統僅供研究與教育用途，**不構成投資建議**。
策略勝率為歷史模擬，不保證未來表現；任何下單都應自行判斷風險。
