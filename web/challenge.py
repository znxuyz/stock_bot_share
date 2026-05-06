"""選股挑戰：加入挑戰 + 週五自動結算（無 Discord 推播）。"""
import logging
from datetime import timedelta

import config
import db
from stock_analyzer import get_latest_price
from time_utils import tw_now

logger = logging.getLogger(__name__)


def add(sid, uid=None, guild_id=None):
    uid      = uid      or config.USER_ID
    guild_id = guild_id or config.GUILD_ID
    sid      = sid.strip().upper()

    week_key = tw_now().strftime('%Y-W%W')
    existing = db.get_challenge(guild_id, uid, week_key)
    if existing:
        return {
            'ok': True, 'duplicate': True,
            'sid':         existing['sid'],
            'start_price': float(existing['start_price']),
            'end_date':    str(existing['end_date']),
        }

    start_price = get_latest_price(sid)
    if start_price is None:
        return {'ok': False, 'error': f'無法取得 {sid} 的最新價格，請確認代號'}

    now_d = tw_now().date()
    days_to_fri = (4 - now_d.weekday()) % 7
    if days_to_fri == 0:
        days_to_fri = 7
    end_date = (now_d + timedelta(days=days_to_fri)).isoformat()

    db.add_challenge(guild_id, uid, week_key, sid, start_price, end_date)

    return {
        'ok': True,
        'sid': sid,
        'start_price': start_price,
        'end_date': end_date,
        'week_key': week_key,
    }


def list_current(guild_id=None):
    guild_id = guild_id or config.GUILD_ID
    week_key = tw_now().strftime('%Y-W%W')
    rows = db.get_all_challenges(guild_id, week_key)
    out = []
    for ch in rows:
        cur = get_latest_price(ch['sid'])
        start = float(ch['start_price'])
        pct = round((cur - start) / start * 100, 2) if cur else None
        out.append({
            'user_id':     ch['user_id'],
            'sid':         ch['sid'],
            'start_price': start,
            'end_date':    str(ch['end_date']) if ch['end_date'] else None,
            'cur_price':   cur,
            'change_pct':  pct,
        })
    out.sort(key=lambda x: (x['change_pct'] is None, -(x['change_pct'] or 0)))
    return {'week_key': week_key, 'items': out}


def settle_now(guild_id=None):
    """週五 21:00 自動呼叫；也可以手動觸發。結算後清空當週紀錄（與 my_stock_bot 行為相同）。"""
    guild_id = guild_id or config.GUILD_ID
    week_key = tw_now().strftime('%Y-W%W')
    rows = db.get_all_challenges(guild_id, week_key)

    results = []
    for ch in rows:
        cur = get_latest_price(ch['sid'])
        if cur is None:
            continue
        start = float(ch['start_price'])
        pct   = round((cur - start) / start * 100, 2)
        results.append({
            'user_id': ch['user_id'], 'sid': ch['sid'],
            'start_price': start, 'cur_price': cur, 'change_pct': pct,
        })

    if results:
        results.sort(key=lambda x: x['change_pct'], reverse=True)
        try:
            db.clear_challenges(guild_id, week_key)
        except Exception as e:
            logger.warning('[挑戰] 清空失敗：%s', e)

    logger.info('[挑戰] 週結算完成，共 %d 筆', len(results))
    return {'week_key': week_key, 'results': results, 'count': len(results)}
