# `tests/` ── 單元測試

純邏輯測試，**不會打 TWSE 也不會碰真的資料庫**。
跑得很快（<10 秒），可以放心隨時跑。

## 怎麼跑

```bash
# 在 repo 根目錄
pip install pytest
python -m pytest tests/ -v
```

順便靜態檢查（可選）：
```bash
pip install pyflakes
python -m pyflakes *.py db/*.py web/*.py tests/*.py
```

## 測試檔對照

| 檔案 | 測什麼 |
|---|---|
| `conftest.py` | pytest 共用 fixture |
| `test_imports.py` | 確保所有模組可以被 import（最便宜的 smoke test） |
| `test_indicators.py` | EMA / 量比 / RSI / MACD 等指標公式 |
| `test_scoring.py` | 8 項評分加減項邏輯 |
| `test_chase.py` | 連 ≥ 3 日漲停的「強勢追漲」分支 |
| `test_entry_zone.py` | 隔日合理進場區間計算 |
| `test_filter_first_round.py` | 第 1 輪基本門檻篩選 |
| `test_topflow.py` | 外資 / 投信 Top 買賣超 |
| `test_settle.py` | 1 週 / 2 週結算邏輯 |
| `test_last_run.py` | `LAST_RUN` 共用狀態執行緒安全 |
| `test_logging_setup.py` | logger 初始化 / 格式 |
| `test_time_utils.py` | 台北時區 / 交易日判斷 |

## 我加了新功能要寫測試嗎？

**核心策略邏輯（scoring / chase / entry_zone / matching）改動就要補測試**。
HTTP / DB 那層是 I/O 重，不必硬寫單測。
