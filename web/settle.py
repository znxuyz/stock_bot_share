"""
週五 18:00 結算 settle_weekly（純網頁版，移除 Discord webhook 推播）。
從 actual_entry_date ~ settle_date 抓 K 棒，掃 high/low 判斷是否觸 target/stop。
"""
import logging

import config
import db
from matching import get_period_kbars

logger = logging.getLogger(__name__)


def _compute_missed_hypothetical(settle_date, guild_id):
    """對 settle1_date = settle_date 的 missed 紀錄，補算「假設有買到」的結算結果。"""
    rows = db.get_missed_for_hypothetical(settle_date, guild_id)
    if not rows:
        return 0
    n = 0
    for r in rows:
        try:
            entry      = float(r['t1_open_price'])
            entry_date = r['actual_entry_date']
            if entry_date is None:
                continue
            df = get_period_kbars(r['sid'], entry_date, settle_date)
            if df.empty:
                continue
            settle_close = float(df.iloc[-1]['close'])
            pct = round((settle_close - entry) / entry * 100, 2)
            db.update_missed_hypothetical(r['id'], settle_close, pct)
            n += 1
        except Exception as e:
            logger.warning('[結算/missed假設] %s 補算失敗：%s', r.get('sid'), e)
    if n:
        logger.info('[結算/missed假設] %s 補算 %d 筆', settle_date, n)
    return n


def settle_weekly(settle_date, round_num, guild_id=None):
    """
    結算 settle_date 這天到期的第 round_num 次結算。
    回傳結果 dict 列表（給觸發者顯示用）。
    """
    guild_id = guild_id or config.GUILD_ID

    if round_num == 1:
        try:
            _compute_missed_hypothetical(settle_date, guild_id)
        except Exception as e:
            logger.warning('[結算/missed假設] %s 整體失敗：%s', settle_date, e)

    records = db.get_pending_settle(settle_date, round_num, guild_id)
    if not records:
        logger.info('[結算] %s 第%d次：無待結算記錄', settle_date, round_num)
        return []

    results = []
    for r in records:
        actual_entry      = float(r['actual_entry_price'])
        actual_entry_date = r['actual_entry_date']
        t1 = float(r['actual_target1'])    if r['actual_target1']    else None
        t2 = float(r['actual_target2'])    if r['actual_target2']    else None
        sl = float(r['actual_stop_loss']) if r['actual_stop_loss'] else None

        df = get_period_kbars(r['sid'], actual_entry_date, settle_date)
        if df.empty:
            logger.warning('[結算] %s 抓不到 K 棒，跳過', r['sid'])
            continue
        last_row     = df.iloc[-1]
        settle_close = float(last_row['close'])

        hit_t1 = hit_t2 = hit_sl = False
        hit_t1_date = hit_t2_date = hit_sl_date = None
        for row in df.itertuples(index=False):
            d  = row.date
            hi = float(row.high)
            lo = float(row.low)
            if t1 and not hit_t1 and hi >= t1: hit_t1, hit_t1_date = True, d
            if t2 and not hit_t2 and hi >= t2: hit_t2, hit_t2_date = True, d
            if sl and not hit_sl and lo <= sl: hit_sl, hit_sl_date = True, d

        if hit_sl:
            settle_pct = round((sl - actual_entry) / actual_entry * 100, 2)
        else:
            settle_pct = round((settle_close - actual_entry) / actual_entry * 100, 2)

        db.update_settle(
            r['id'], round_num, settle_close,
            hit_t1, hit_t2, hit_sl,
            hit_t1_date, hit_t2_date, hit_sl_date,
            settle_pct=settle_pct,
        )
        results.append({
            'sid':   r['sid'], 'name': r.get('name', ''),
            'grade': r['grade'],
            'actual_entry': actual_entry,
            'settle_close': settle_close,
            'settle_pct':   settle_pct,
            'target1': t1, 'target2': t2, 'stop_loss': sl,
            'hit_target1': hit_t1, 'hit_target2': hit_t2, 'hit_stoploss': hit_sl,
            'position_pct': float(r['position_pct']) if r['position_pct'] else 0,
        })

    logger.info('[結算] %s 第%d次完成，%d 筆', settle_date, round_num, len(results))
    return results
