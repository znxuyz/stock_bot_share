"""
背景排程（純網頁版，無 Discord）：
  - 平日 17:00 觸發盤後分析（用 DB 狀態避免重啟重複觸發）
  - 週五 18:00 兩次結算（settle_weekly）
  - 週五 21:00 挑戰結算
"""
import logging
import threading
import time
from datetime import timedelta

import config
import db
from time_utils import tw_now

from web.state import update_last_run

logger = logging.getLogger(__name__)


def _run_analysis_with_status(attempt=0, mode='auto'):
    """包一層：用 DB 狀態管理避免服務重啟造成的重複觸發。"""
    from analysis import run_analysis
    today = tw_now().date()
    try:
        db.record_run_start(today, attempt)
    except Exception as e:
        logger.warning('[排程] record_run_start 失敗：%s', e)

    try:
        status = run_analysis(attempt=attempt, run_mode=mode) or 'fail'
    except Exception as e:
        status = 'fail'
        logger.error('[排程] run_analysis 例外：%s', e)

    try:
        db.record_run_end(today, status)
    except Exception as e:
        logger.warning('[排程] record_run_end 失敗：%s', e)

    update_last_run(time=tw_now(), date=today, mode=mode,
                    status=status, attempt=attempt)
    logger.info('[排程] run_analysis 結果：status=%s attempt=%d', status, attempt)


def _do_friday_settle(d):
    """週五兩次結算 + 推 dashboard。"""
    from web.settle import settle_weekly
    try:
        settle_weekly(d, 1, config.GUILD_ID)
        time.sleep(1)
        settle_weekly(d, 2, config.GUILD_ID)
        time.sleep(1)
    except Exception as e:
        logger.error('[結算] 失敗：%s', e)
    try:
        import web_export as _we
        _we.export_dashboard()
    except Exception as e:
        logger.error('[Web] 結算後 Dashboard 匯出失敗：%s', e)


def _do_challenge_settle():
    from web.challenge import settle_now
    try:
        settle_now(config.GUILD_ID)
    except Exception as e:
        logger.error('[挑戰結算] 失敗：%s', e)


def scheduler():
    boot_time         = time.time()
    last_check_minute = None
    fired             = set()

    while True:
        if time.time() - boot_time < config.SCHEDULER_STARTUP_BUFFER_SEC:
            time.sleep(10)
            continue

        now = tw_now()
        h, wd, mn = now.hour, now.weekday(), now.minute

        # 平日盤後分析
        if wd < 5 and (h, mn) in config.ANALYSIS_TRIGGER_TIMES:
            check_key = (now.date(), h, mn)
            if check_key != last_check_minute:
                last_check_minute = check_key
                today = now.date()
                try:
                    can_run, attempt, reason = db.can_run_today(today, now)
                    logger.info('[排程] %02d:%02d can_run=%s attempt=%d reason=%s',
                                h, mn, can_run, attempt, reason)
                    if can_run:
                        threading.Thread(
                            target=_run_analysis_with_status,
                            kwargs={'attempt': attempt, 'mode': 'auto'},
                            daemon=True,
                        ).start()
                except Exception as e:
                    logger.error('[排程] 檢查狀態失敗：%s', e)
                    if (h, mn) == (17, 0):
                        threading.Thread(
                            target=_run_analysis_with_status,
                            kwargs={'attempt': 0, 'mode': 'auto'},
                            daemon=True,
                        ).start()

        # 週五 18:00 結算
        if wd == 4 and h == 18 and mn == 0:
            k = (now.date(), 'weekly_settle')
            if k not in fired:
                fired.add(k)
                threading.Thread(target=_do_friday_settle, args=(now.date(),), daemon=True).start()

        # 週五 21:00 挑戰結算
        if wd == 4 and h == 21 and mn == 0:
            k = (now.date(), 'challenge_settle')
            if k not in fired:
                fired.add(k)
                threading.Thread(target=_do_challenge_settle, daemon=True).start()

        # 每天清掉 7 天前的 fired key
        if h == 0 and mn == 1:
            cutoff = now.date() - timedelta(days=7)
            fired  = {k for k in fired if k[0] >= cutoff}

        time.sleep(60)
