"""
Shared database connection for NBA load scripts.
Loads .env from project root and exposes get_engine().
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine

# Load .env from project root (parent of source/)
_script_dir = Path(__file__).resolve().parent
_env_path = _script_dir.parent / ".env"
load_dotenv(_env_path)


def get_engine(use_test: bool = False):
    """Return a SQLAlchemy engine for nba_db (default) or nba_db_test."""
    url_key = "DATABASE_TEST_URL" if use_test else "DATABASE_URL"
    url = os.environ.get(url_key)
    if not url:
        raise RuntimeError(f"Missing {url_key} in environment or .env")
    return create_engine(url)
