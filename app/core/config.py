"""Root-anchored resources and existing startup configuration."""

import os
from pathlib import Path

from app.core.proxy import ProxyPolicy
from app.core.rate_limits import rate_settings

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"
MAX_BODY_BYTES = 20_000
RATE_LIMIT, RATE_WINDOW, RATE_MAX_CLIENTS = rate_settings(os.environ)
PROXY_POLICY = ProxyPolicy.from_env(os.environ)


def database_path() -> str:
    return os.getenv("EVENTRA_DB_PATH", str(PROJECT_ROOT / "data" / "eventra.sqlite3"))
