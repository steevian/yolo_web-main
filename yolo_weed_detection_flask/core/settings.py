import os
from dataclasses import dataclass


@dataclass
class AppConfig:
    host: str
    port: int
    sqlite_db_path: str
    sqlite_timeout: float = 10.0


def _resolve_sqlite_path(base_dir: str, db_path: str) -> str:
    if os.path.isabs(db_path):
        return db_path
    return os.path.join(base_dir, db_path)


def get_app_config(base_dir: str) -> AppConfig:
    host = os.getenv('FLASK_HOST', '0.0.0.0')

    try:
        port = int(os.getenv('PORT', '8080'))
    except ValueError:
        port = 8080

    sqlite_db_path = _resolve_sqlite_path(
        base_dir,
        os.getenv('SQLITE_DB_PATH', 'weed_detection.db'),
    )

    return AppConfig(
        host=host,
        port=port,
        sqlite_db_path=sqlite_db_path,
    )
