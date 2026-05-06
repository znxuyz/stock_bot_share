"""持倉 / 買 / 賣 / 排行榜（純資料；HTTP 那層負責序列化）。"""
import config
import db
from stock_analyzer import get_latest_price
from time_utils import tw_now


def get_holding_view(uid=None, uname=None, guild_id=None):
    """回傳目前持倉與已實現損益的結構化 dict（整段 my_stock_bot/discord_bot 文字邏輯改成資料）。"""
    uid     = uid     or config.USER_ID
    uname   = uname   or config.USER_NAME
    guild_id = guild_id or config.GUILD_ID

    rows = db.get_holdings(guild_id, uid)
    items = []
    total_cost = total_mkt = total_unreal = 0.0
    for h in rows:
        cost = float(h['price']) * int(h['shares'])
        cur  = get_latest_price(h['sid'])
        item = {
            'id':       h['id'],
            'sid':      h['sid'],
            'price':    float(h['price']),
            'shares':   int(h['shares']),
            'buy_date': h['buy_date'].isoformat() if h['buy_date'] else None,
            'cost':     round(cost, 2),
            'cur':      cur,
            'market_value': None,
            'unrealized':   None,
            'change_pct':   None,
        }
        if cur is not None:
            mkt    = cur * int(h['shares'])
            unreal = mkt - cost
            pct    = (cur - float(h['price'])) / float(h['price']) * 100 if float(h['price']) else 0
            item['market_value'] = round(mkt, 2)
            item['unrealized']   = round(unreal, 2)
            item['change_pct']   = round(pct, 2)
            total_mkt    += mkt
            total_unreal += unreal
        total_cost += cost
        items.append(item)

    return {
        'user_name':   uname,
        'items':       items,
        'total_cost':  round(total_cost,  2),
        'total_value': round(total_mkt,   2),
        'total_unrealized': round(total_unreal, 2),
        'total_realized':   round(db.get_pnl(guild_id, uid), 2),
    }


def buy(sid, price, shares, uid=None, guild_id=None):
    uid      = uid      or config.USER_ID
    guild_id = guild_id or config.GUILD_ID
    sid      = sid.strip().upper()
    price    = float(price)
    shares   = int(shares)
    if price <= 0 or shares <= 0:
        return {'ok': False, 'error': '價格與股數必須 > 0'}
    db.add_holding(guild_id, uid, sid, price, shares, tw_now().date())
    return {
        'ok': True,
        'sid': sid, 'price': price, 'shares': shares,
        'cost': round(price * shares, 2),
    }


def sell(sid, price, shares, uid=None, guild_id=None):
    uid      = uid      or config.USER_ID
    guild_id = guild_id or config.GUILD_ID
    sid      = sid.strip().upper()
    price    = float(price)
    shares   = int(shares)
    if price <= 0 or shares <= 0:
        return {'ok': False, 'error': '價格與股數必須 > 0'}
    realized, err = db.remove_holding(guild_id, uid, sid, price, shares)
    if err:
        return {'ok': False, 'error': err}
    return {
        'ok': True,
        'sid': sid, 'price': price, 'shares': shares,
        'realized': round(realized, 2),
        'total_realized': round(db.get_pnl(guild_id, uid), 2),
    }


def leaderboard_view(guild_id=None):
    """單人版只會有一行，但保留 API 以便未來擴充。"""
    guild_id = guild_id or config.GUILD_ID
    rows = db.get_leaderboard(guild_id)
    return [
        {'user_id': r['user_id'], 'total_pnl': float(r['total_pnl'])}
        for r in rows
    ]
