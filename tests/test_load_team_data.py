"""
Tests for load_team_data.

Unit tests: no DB, no cleanup. Run from project/:  pytest tests/ -v -m "not integration"
Integration test: uses test DB, truncates before and after. Run from project/:  pytest tests/ -v -m integration
"""
import pandas as pd
import pytest
from sqlalchemy import text

from source.db import get_engine
from source.load_team_data import _data_dir, get_team_df, load_teams


# ----- Unit tests (no database) -----


def test_team_csv_exists_and_has_expected_shape():
    """Team CSV should exist and have 30 rows and expected columns."""
    path = _data_dir / "team_info.csv"
    assert path.exists(), f"Expected data file at {path}"
    df = pd.read_csv(path)
    assert len(df) == 30, "team_info.csv should have 30 teams"
    expected = {"TEAM_ID", "TEAM_NAME", "TEAM_ABBREVIATION", "TEAM_CITY", "TEAM_CONFERENCE", "TEAM_DIVISION"}
    assert expected.issubset(set(df.columns)), f"Missing columns: {expected - set(df.columns)}"


def test_get_team_df_returns_prepared_dataframe():
    """get_team_df() returns 30 rows, lowercase columns, no duplicates on team_id."""
    df = get_team_df()
    assert len(df) == 30
    assert all(c.islower() for c in df.columns), "columns should be lowercase"
    assert df["team_id"].is_unique, "team_id should be unique"
    assert "team_id" in df.columns and "team_name" in df.columns


# ----- Integration test (uses test DB; truncates before and after) -----


@pytest.mark.integration
def test_load_teams_into_test_db():
    """Load teams into test DB, verify count, then truncate so test DB is clean."""
    engine = get_engine(use_test=True)
    try:
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE team CASCADE"))
            conn.commit()
        n = load_teams(engine)
        assert n == 30
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM team"))
            count = result.scalar()
        assert count == 30
    finally:
        # Teardown: delete what we added so test DB is clean for next run
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE team CASCADE"))
            conn.commit()
