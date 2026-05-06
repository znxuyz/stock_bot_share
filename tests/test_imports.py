"""所有公開模組 import smoke test：保證 PR 不會打破基本載入。"""


def test_top_level_modules_import():
    import importlib
    for name in ('app', 'analysis', 'matching', 'config', 'db',
                 'web', 'web_export', 'logging_setup', 'entry_zone',
                 'stock_analyzer'):
        m = importlib.import_module(name)
        assert m is not None, f'{name} import returned None'


def test_db_package_exports():
    import db
    expected = [
        'get_conn', 'is_available', 'init_db',
        'record_run_start', 'record_run_end', 'can_run_today',
        'save_screen_records', 'determine_t1_fill', 'fill_t1_entry',
        'get_pending_settle', 'update_settle',
        'get_missed_for_hypothetical', 'update_missed_hypothetical',
        'get_missed_hypothetical_stats',
        'get_cumulative_stats', 'get_aggregated_stats',
        'get_holdings', 'add_holding', 'remove_holding',
        'get_challenge', 'add_challenge', 'clear_challenges',
    ]
    for name in expected:
        assert hasattr(db, name), f'db package missing {name}'


def test_web_package_exports():
    import web
    from web.state import get_last_run, update_last_run
    assert callable(web.WebHandler)
    assert callable(web.scheduler)
    assert isinstance(web.LAST_RUN, dict)
    assert callable(update_last_run)
    assert callable(get_last_run)


def test_analysis_exports():
    import analysis
    expected = ['run_analysis', 'INDICATOR_GUIDE']
    for name in expected:
        assert hasattr(analysis, name), f'analysis missing {name}'


def test_stock_analyzer_exports():
    import stock_analyzer
    for name in ('analyze_stock_data', 'stock_api_get', 'fetch_top_traders', 'get_latest_price'):
        assert hasattr(stock_analyzer, name), f'stock_analyzer missing {name}'
