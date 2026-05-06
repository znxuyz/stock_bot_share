"""
川投顧量化系統（純網頁版）── 進入點。
取代 my_stock_bot/bot.py。

啟動：
  - 起 HTTP server（監聽 PORT）
  - 起背景 scheduler thread（17:00 / 週五結算）
  - 啟動瞬間順便推一次 dashboard，保持 GitHub Pages 同步

環境變數：
  PORT             HTTP 監聽 port（Railway 自動注入；預設 8080）
  DATABASE_URL     PostgreSQL 連線字串
  GITHUB_TOKEN     Fine-grained PAT（contents read+write，給 dashboard 用）
  GITHUB_REPO      你的 GitHub repo，例如 your-name/your-repo（必填）
  GITHUB_BRANCH    預設 main
  BOT_PUBLIC_URL   給 dashboard 個股查詢用的本服務外部網址
  WEB_PASSWORD     寫入操作密碼（留空即不啟用驗證）
  USER_NAME        持倉顯示用名稱（預設「爸爸」）
"""
import logging
import threading
import time
from http.server import ThreadingHTTPServer

import config
from logging_setup import setup_logging

setup_logging()

import db
from web import WebHandler, scheduler

logger = logging.getLogger(__name__)


def _startup_export():
    """服務啟動後讓 dashboard 立刻同步一次（內容無變動時 GitHub 端會跳過 commit）。"""
    time.sleep(5)
    try:
        import web_export as _we
        _we.export_dashboard()
    except Exception as e:
        logger.error('[Web] 啟動時 Dashboard 匯出失敗：%s', e)


def main():
    if config.DATABASE_URL:
        try:
            db.init_db()
        except Exception as e:
            logger.error('[DB] 初始化失敗：%s', e)
    else:
        logger.warning('[DB] DATABASE_URL 未設定，跳過資料庫初始化')

    threading.Thread(target=scheduler,        daemon=True).start()
    threading.Thread(target=_startup_export, daemon=True).start()

    if config.WEB_PASSWORD:
        logger.info('[Web] 已啟用 Basic Auth（WEB_PASSWORD 已設定）')
    else:
        logger.warning('[Web] 未設定 WEB_PASSWORD，所有 POST 端點對外開放')

    logger.info('[Web] 已啟動，監聽 port %d', config.PORT)
    ThreadingHTTPServer(('0.0.0.0', config.PORT), WebHandler).serve_forever()


if __name__ == '__main__':
    main()
