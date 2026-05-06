"""
HTTP 路由（純網頁版）。取代 my_stock_bot/discord_bot/handlers.py。

GET：
  /                      → 對外健康檢查 OK（dashboard 由 GitHub Pages serve）
  /api/stock?sid=2330    → 個股查詢（CORS 開放）
  /api/topbuyer          → 外資買超 Top 10
  /api/topseller         → 外資賣超 Top 10
  /api/holding           → 目前持倉 + 損益
  /api/challenges        → 本週挑戰列表
  /api/last_run          → 最後一次分析狀態
  /api/report            → 累積統計
  /api/stats             → 詳細統計

POST（需要 WEB_PASSWORD）：
  /api/run               → 觸發盤後分析（背景）
  /api/buy               → {"sid","price","shares"}
  /api/sell              → {"sid","price","shares"}
  /api/challenge         → {"sid"}
  /api/challenge/settle  → 手動結算本週挑戰
"""
import json
import logging
import threading
from http.server import BaseHTTPRequestHandler

from time_utils import get_target_date, tw_now
from web.auth import require_auth
from web.state import get_last_run, update_last_run

logger = logging.getLogger(__name__)


class WebHandler(BaseHTTPRequestHandler):
    """純網頁 HTTP 端點。"""

    def log_message(self, fmt, *args):
        pass

    # ─────────── 共用 ───────────
    def _send_json(self, code, body, cors=True):
        data = json.dumps(body, ensure_ascii=False, default=str).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(data))
        if cors:
            self.send_header('Access-Control-Allow-Origin',  '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type')
            self.send_header('Cache-Control',                'no-store')
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self):
        length = int(self.headers.get('Content-Length', 0))
        if not length:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode('utf-8') or '{}')
        except Exception:
            return {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin',  '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type')
        self.send_header('Access-Control-Max-Age',       '600')
        self.end_headers()

    # ─────────── GET ───────────
    def do_GET(self):
        from urllib.parse import parse_qs, urlparse
        u  = urlparse(self.path)
        qs = parse_qs(u.query or '')

        # /api/stock
        if u.path == '/api/stock':
            from stock_analyzer import stock_api_get
            sid   = (qs.get('sid', [''])[0] or '').strip().upper()
            force = (qs.get('force', ['0'])[0] or '0').lower() in ('1', 'true', 'yes')
            if not sid or not sid.isalnum() or len(sid) > 6:
                self._send_json(400, {'ok': False, 'error': '請提供有效的股票代號（最多 6 碼）'})
                return
            data = stock_api_get(sid, force=force)
            if data is None:
                self._send_json(404, {'ok': False, 'error': f'查無 {sid} 資料'})
                return
            self._send_json(200, {'ok': True, 'data': data})
            return

        if u.path in ('/api/topbuyer', '/api/topseller'):
            from stock_analyzer import fetch_top_traders
            top_type = 'buy' if u.path.endswith('topbuyer') else 'sell'
            data, date_str = fetch_top_traders(top_type)
            if data is None:
                self._send_json(404, {'ok': False, 'error': f'無資料（{date_str}）'})
                return
            self._send_json(200, {'ok': True, 'data': data, 'date': date_str})
            return

        if u.path == '/api/holding':
            from web.portfolio import get_holding_view
            self._send_json(200, {'ok': True, 'data': get_holding_view()})
            return

        if u.path == '/api/challenges':
            from web.challenge import list_current
            self._send_json(200, {'ok': True, 'data': list_current()})
            return

        if u.path == '/api/last_run':
            snap = get_last_run()
            if snap.get('time'):
                snap['time'] = snap['time'].isoformat() if hasattr(snap['time'], 'isoformat') else str(snap['time'])
            if snap.get('date'):
                snap['date'] = snap['date'].isoformat() if hasattr(snap['date'], 'isoformat') else str(snap['date'])
            self._send_json(200, {'ok': True, 'data': snap})
            return

        if u.path == '/api/report':
            from web.stats_view import report
            self._send_json(200, report())
            return

        if u.path == '/api/stats':
            from web.stats_view import stats
            self._send_json(200, stats())
            return

        # 健康檢查
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(b'OK - stock_bot_share')

    # ─────────── POST ───────────
    def do_POST(self):
        from urllib.parse import urlparse
        u = urlparse(self.path)

        if u.path == '/api/run':
            if not require_auth(self):
                return
            self._handle_run()
            return

        if u.path == '/api/buy':
            if not require_auth(self):
                return
            body = self._read_json()
            from web.portfolio import buy
            self._send_json(200, buy(
                body.get('sid', ''), body.get('price'), body.get('shares')
            ))
            return

        if u.path == '/api/sell':
            if not require_auth(self):
                return
            body = self._read_json()
            from web.portfolio import sell
            self._send_json(200, sell(
                body.get('sid', ''), body.get('price'), body.get('shares')
            ))
            return

        if u.path == '/api/challenge':
            if not require_auth(self):
                return
            body = self._read_json()
            from web.challenge import add
            self._send_json(200, add(body.get('sid', '')))
            return

        if u.path == '/api/challenge/settle':
            if not require_auth(self):
                return
            from web.challenge import settle_now
            self._send_json(200, {'ok': True, 'data': settle_now()})
            return

        self._send_json(404, {'ok': False, 'error': 'unknown endpoint'})

    # ─────────── 觸發分析 ───────────
    def _handle_run(self):
        body = self._read_json()
        mode = (body.get('mode') or 'auto').strip().lower()

        snap = get_last_run()
        if snap.get('status') == 'running':
            self._send_json(409, {'ok': False, 'error': '上一次分析仍在執行中', 'last': snap})
            return

        target_date = get_target_date(mode)
        update_last_run(time=tw_now(), mode=mode, date=target_date,
                        status='running', error=None)

        def _bg():
            from analysis import run_analysis
            try:
                status = run_analysis(run_mode=mode) or 'fail'
                update_last_run(status=status)
            except Exception as e:
                logger.error('[/api/run] 失敗：%s', e)
                update_last_run(status='error', error=str(e))

        threading.Thread(target=_bg, daemon=True).start()
        self._send_json(202, {'ok': True, 'mode': mode, 'target_date': target_date,
                              'message': '已開始執行，預計 3-5 分鐘'})
