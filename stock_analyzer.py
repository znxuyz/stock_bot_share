"""
個股分析（純資料）。供 /api/stock 與 dashboard 使用。
從 my_stock_bot/discord_bot/stock_commands.py 抽出計算邏輯，移除 Discord 文字格式化。
"""
import logging
import time

import config
from advanced_indicators import calc_advanced_indicators
from chase import check_strong_chase, count_consecutive_limit_ups
from entry_zone import calc_entry_zone
from indicators import (
    calc_bias_and_entry, calc_macd, calc_volume_ratio, check_ema_bull,
)
from scoring import calc_chip_concentration, calc_score
from time_utils import get_target_date, prev_months, tw_now
from twse_kbar import build_history_fast, fetch_stock_day_fast
from twse_t86 import fetch_t86_cached

logger = logging.getLogger(__name__)


_STOCK_API_CACHE = {}


def _grade_from_score(score):
    if score >= 85: return 'SS', '🔥', '各項指標多數達標，可考慮進場布局。'
    if score >= 68: return 'S',  '💎', '條件不錯但非最佳，小量試水溫。'
    if score >= 52: return 'A',  '📈', '訊號普通，建議等待更明確訊號再進場。'
    return None, '', '條件偏弱，暫時觀望。'


def analyze_stock_data(sid):
    """完整個股分析 → 回 dict（給 /api/stock 用），失敗回 None。"""
    sid = sid.strip().upper()

    today_str = tw_now().strftime('%Y%m%d')
    months = prev_months(today_str, n=6)
    df_all = build_history_fast(sid, months)
    if df_all.empty or 'date' not in df_all.columns or len(df_all) < 10:
        return None

    latest_kbar_date = df_all['date'].iloc[-1].isoformat() if not df_all.empty else None
    kbar_count       = len(df_all)

    price      = float(df_all['close'].iloc[-1])
    prev_close = float(df_all['close'].iloc[-2])
    diff       = price - prev_close
    change     = round(diff / prev_close * 100, 2) if prev_close else 0.0
    vol_ratio  = calc_volume_ratio(df_all, df_all['date'].iloc[-1])
    is_bull, ema_mode = check_ema_bull(df_all)

    foreign = trust = None
    try:
        date_str = get_target_date('auto')
        df_i = fetch_t86_cached(date_str)
        if df_i is not None and not df_i.empty and '_foreign' in df_i.columns:
            row = df_i[df_i['sid_clean'] == sid]
            if not row.empty:
                foreign = int(row['_foreign'].values[0])
                trust   = int(row['_trust'].values[0])
    except Exception as e:
        logger.warning('[/stock] 取法人資料失敗：%s', e)

    bias = calc_bias_and_entry(df_all, price)
    adv  = calc_advanced_indicators(df_all, price)
    macd = calc_macd(df_all)
    chip = {}
    if foreign is not None:
        vol_last = int(df_all['volume'].iloc[-1]) if not df_all.empty else 0
        chip = calc_chip_concentration(foreign or 0, trust or 0, vol_last)

    consec = count_consecutive_limit_ups(df_all)

    entry = {
        'change':       change,
        'vol_ratio':    vol_ratio,
        'foreign':      foreign or 0,
        'trust':        trust or 0,
        'bias':         bias,
        'adv':          adv,
        'chip_score':   chip.get('score', 0),
        'macd_score':   macd.get('macd_score', 5),
        'market_score': 0,
        'margin_score': 0,
        'consec_score': 0,
    }
    score = calc_score(entry)
    grade, grade_emoji, rec = _grade_from_score(score)

    chase_mode  = 'normal'
    chase_check = None
    if consec >= 3:
        chase = check_strong_chase(entry, macd, entry.get('market_score', 0))
        chase_check = chase
        if   chase['passed'] >= 5: chase_mode = 'strong_chase'
        elif chase['passed'] >= 4: chase_mode = 'watch'
        else:                       chase_mode = 'reject'

    zone_low, zone_high = calc_entry_zone(price, chase_mode, grade=grade, precision=1)

    return {
        'sid':       sid,
        'price':     round(price, 2),
        'prev_close': round(prev_close, 2),
        'diff':      round(diff, 2),
        'change':    change,
        'vol_ratio': round(float(vol_ratio), 2) if vol_ratio is not None else None,
        'ema_mode':  ema_mode,
        'foreign':   foreign,
        'trust':     trust,
        'bias':      bias,
        'adv':       {k: v for k, v in adv.items() if not callable(v)},
        'macd':      macd,
        'chip':      chip,
        'consec_limit_up': consec,
        'chase_mode':      chase_mode,
        'chase_check':     chase_check,
        'entry_zone_low':  zone_low,
        'entry_zone_high': zone_high,
        'est_target1':     round(price * 1.05, 1),
        'est_target2':     round(price * 1.10, 1),
        'est_stop_loss':   round(price * 0.95, 1),
        'score':       score,
        'grade':       grade,
        'grade_emoji': grade_emoji,
        'rec':         rec,
        'latest_kbar_date': latest_kbar_date,
        'kbar_count':       kbar_count,
        'queried_at':       tw_now().strftime('%Y-%m-%d %H:%M:%S'),
    }


def stock_api_get(sid, force=False):
    """Web /api/stock：含 15 分鐘記憶體快取。"""
    now = time.time()
    if not force and sid in _STOCK_API_CACHE:
        ts, data = _STOCK_API_CACHE[sid]
        if now - ts < config.STOCK_API_CACHE_TTL_SEC:
            data = dict(data)
            data['_from_cache'] = True
            return data
    data = analyze_stock_data(sid)
    if data is not None:
        _STOCK_API_CACHE[sid] = (now, data)
        data['_from_cache'] = False
    return data


def fetch_top_traders(top_type='buy', n=10):
    """/topbuyer / /topseller：抓 T86 共享快取，回傳前 N 名。"""
    date_str = get_target_date('auto')
    df = fetch_t86_cached(date_str)
    if df is None or df.empty or '_foreign' not in df.columns:
        return None, date_str

    name_col = df.columns[1]
    if top_type == 'buy':
        rows = df[df['_foreign'] > 0].sort_values('_foreign', ascending=False).head(n)
    else:
        rows = df[df['_foreign'] < 0].sort_values('_foreign', ascending=True).head(n)

    result = []
    for row_dict in rows.to_dict('records'):
        result.append({
            'sid':     row_dict['sid_clean'],
            'name':    str(row_dict[name_col]).strip(),
            'foreign': int(row_dict['_foreign']),
            'trust':   int(row_dict['_trust']),
        })
    return result, date_str


def get_latest_price(sid):
    """抓 sid 最新收盤價；資料抓不到回 None。"""
    today_str = tw_now().strftime('%Y%m%d')
    df = fetch_stock_day_fast(sid, today_str[:6])
    if df.empty:
        months = prev_months(today_str, n=2)
        if len(months) >= 2:
            df = fetch_stock_day_fast(sid, months[1])
    if df.empty:
        return None
    try:
        return float(df['close'].iloc[-1])
    except Exception:
        return None
