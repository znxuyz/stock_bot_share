"""LAST_RUN：scheduler thread 寫、handler thread 讀；用 lock 保護避免 race。"""
import threading

_LAST_RUN_LOCK = threading.Lock()
_LAST_RUN = {
    'time': None, 'mode': None, 'date': None,
    'status': None, 'error': None, 'attempt': 0,
}

# 向下相容：保留 LAST_RUN 名稱
LAST_RUN = _LAST_RUN


def update_last_run(**kwargs):
    """執行緒安全的 update。允許 keys: time / mode / date / status / error / attempt"""
    with _LAST_RUN_LOCK:
        _LAST_RUN.update(kwargs)


def get_last_run():
    """執行緒安全的 snapshot。回傳 dict 副本。"""
    with _LAST_RUN_LOCK:
        return dict(_LAST_RUN)
