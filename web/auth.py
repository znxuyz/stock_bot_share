"""寫入操作的密碼保護。WEB_PASSWORD 留空則完全不檢查。"""
import base64
import hmac

import config


def is_authed(handler) -> bool:
    """讀 Authorization: Basic header；密碼比對成功 → True。"""
    if not config.WEB_PASSWORD:
        return True
    raw = handler.headers.get('Authorization', '')
    if not raw.startswith('Basic '):
        return False
    try:
        decoded = base64.b64decode(raw[6:]).decode('utf-8')
    except Exception:
        return False
    _, _, pwd = decoded.partition(':')
    return hmac.compare_digest(pwd, config.WEB_PASSWORD)


def require_auth(handler) -> bool:
    """未通過驗證時送 401 並回 False；通過 True。"""
    if is_authed(handler):
        return True
    handler.send_response(401)
    handler.send_header('WWW-Authenticate', 'Basic realm="stock-bot"')
    handler.send_header('Content-Type', 'text/plain; charset=utf-8')
    handler.end_headers()
    handler.wfile.write('需要密碼\n'.encode('utf-8'))
    return False
