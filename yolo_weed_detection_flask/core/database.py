import sqlite3


def get_sqlite_conn(db_path: str, row_factory: bool = False, timeout: float = 10.0) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=timeout)
    if row_factory:
        conn.row_factory = sqlite3.Row

    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA synchronous=NORMAL')
    conn.execute('PRAGMA temp_store=MEMORY')
    conn.execute('PRAGMA busy_timeout=5000')

    return conn
