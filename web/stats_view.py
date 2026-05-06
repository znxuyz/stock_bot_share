"""統計（/api/report、/api/stats）：直接回傳結構化 dict，前端再渲染。"""
import logging
import traceback

import config
import db

logger = logging.getLogger(__name__)


def _to_int(v, default=0):
    try: return int(v) if v is not None else default
    except Exception: return default


def _to_float(v, default=0.0):
    try: return float(v) if v is not None else default
    except Exception: return default


def report(guild_id=None):
    """累積統計：進場率 + 賣錢勝率（按等級 / 乖離分組）。"""
    guild_id = guild_id or config.GUILD_ID
    try:
        grade_rows, bias_rows, _ = db.get_cumulative_stats(guild_id)
        total_n = db.get_total_screened(guild_id)
        return {
            'ok': True,
            'total':   total_n,
            'by_grade': [
                {
                    'grade':    g['grade'],
                    'total':    _to_int(g['total']),
                    'filled':   _to_int(g['filled']),
                    'missed':   _to_int(g['missed']),
                    'pending':  _to_int(g['pending']),
                    'settled1': _to_int(g['settled1']),
                    'win1':     _to_int(g['win1']),
                    'avg_ret1': _to_float(g['avg_ret1']),
                    'hit_t1':   _to_int(g['hit_t1']),
                    'hit_t2':   _to_int(g['hit_t2']),
                    'hit_sl':   _to_int(g['hit_sl']),
                }
                for g in grade_rows
            ],
            'by_bias': [
                {
                    'bias_zone': b['bias_zone'],
                    'total':     _to_int(b['total']),
                    'filled':    _to_int(b['filled']),
                    'missed':    _to_int(b['missed']),
                    'settled':   _to_int(b['settled']),
                    'win':       _to_int(b['win']),
                    'avg_ret':   _to_float(b['avg_ret']),
                }
                for b in bias_rows
            ],
        }
    except Exception as e:
        logger.error('[stats.report] %s\n%s', e, traceback.format_exc())
        return {'ok': False, 'error': str(e)}


def stats(guild_id=None):
    """詳細統計 + 修正建議。"""
    guild_id = guild_id or config.GUILD_ID
    try:
        grade_rows, bias_rows, dual_rows = db.get_cumulative_stats(guild_id)
        total_n = db.get_total_screened(guild_id)

        suggestions = []
        for g in grade_rows:
            fi = _to_int(g['filled']); mi = _to_int(g['missed'])
            decided = fi + mi
            if decided >= 10 and fi / decided * 100 < 40:
                suggestions.append(
                    f'{g["grade"]} 級進場率 {fi/decided*100:.0f}% (<40%)，'
                    '建議放寬進場區間'
                )
            s1 = _to_int(g['settled1'])
            if s1 >= 10:
                wr = _to_int(g['win1']) / s1 * 100
                ar = _to_float(g['avg_ret1'])
                if g['grade'] == 'A' and wr < 50:
                    suggestions.append('A 級賣錢勝率 <50%，考慮提高分數門檻')
                if g['grade'] == 'SS' and wr > 70:
                    suggestions.append('SS 級勝率 >70%，可考慮加大倉位')
                if ar < -1:
                    suggestions.append(f'{g["grade"]} 級平均報酬為負，需重新評估')
        for b in bias_rows:
            st = _to_int(b['settled'])
            if st >= 10 and b['bias_zone'] == '過高(>8%)' and _to_int(b['win']) / st * 100 < 40:
                suggestions.append('乖離率 >8% 賣錢勝率過低，建議加入硬過濾')

        return {
            'ok': True,
            'total': total_n,
            'by_grade': report(guild_id)['by_grade'],
            'by_bias':  report(guild_id)['by_bias'],
            'by_dual':  [
                {
                    'buy_type': d['buy_type'],
                    'total':    _to_int(d['total']),
                    'filled':   _to_int(d['filled']),
                    'missed':   _to_int(d['missed']),
                    'settled':  _to_int(d['settled']),
                    'win':      _to_int(d['win']),
                    'avg_ret':  _to_float(d['avg_ret']),
                }
                for d in dual_rows
            ],
            'suggestions': suggestions,
        }
    except Exception as e:
        logger.error('[stats.stats] %s\n%s', e, traceback.format_exc())
        return {'ok': False, 'error': str(e)}
