"""
Tests for load_draft_data.

Unit tests: no DB, no cleanup. Run from project/:  pytest tests/test_load_draft_data.py -v -m "not integration"
Integration test: uses test DB, truncates draft before and after. Run from project/:  pytest tests/test_load_draft_data.py -v -m integration
"""
import pandas as pd
import pytest
from sqlalchemy import text

from source.db import get_engine
from source.load_draft_data import (
    _data_dir,
    get_draft_table_columns,
    get_full_player_df,
    load_draft,
    prepare_draft_df,
)


# ----- Unit tests (no database) -----


def test_player_csv_exists_and_has_draft_columns():
    """Player CSV (used for draft) should exist and have required draft columns."""
    path = _data_dir / "player_data_02092026.csv"
    assert path.exists(), f"Expected data file at {path}"
    df = pd.read_csv(path)
    required = {"PERSON_ID", "DRAFT_YEAR", "DRAFT_ROUND", "DRAFT_NUMBER", "TEAM_ID"}
    assert required.issubset(set(df.columns)), f"Missing columns: {required - set(df.columns)}"


def test_get_full_player_df_returns_dataframe_with_draft_columns():
    """get_full_player_df() returns a DataFrame with draft-related columns."""
    df = get_full_player_df()
    assert isinstance(df, pd.DataFrame)
    assert "PERSON_ID" in df.columns and "DRAFT_YEAR" in df.columns and "DRAFT_NUMBER" in df.columns
    assert len(df) > 0


def test_prepare_draft_df_selects_columns_renames_and_filters_by_draft_year():
    """prepare_draft_df keeps only draft table columns, renames to DB names (DRAFT_NUMBER -> draft_pick), and filters by draft_year."""
    table_columns = ["player_id", "draft_year", "draft_round", "draft_pick", "team_id"]
    full_df = pd.DataFrame({
        "PERSON_ID": [1, 2, 3],
        "DRAFT_YEAR": [1998, 2003, 2011],
        "DRAFT_ROUND": [1, 2, 1],
        "DRAFT_NUMBER": [5, 35, 12],
        "TEAM_ID": [1610612737, 1610612738, 1610612737],
    })
    out = prepare_draft_df(full_df, table_columns, start_year=2000, end_year=2010)
    assert set(out.columns) == set(table_columns), "output should have exactly the table columns (order may vary)"
    assert "draft_pick" in out.columns, "DRAFT_NUMBER should be renamed to draft_pick"
    assert out["player_id"].tolist() == [2]  # only 2003 is in (2000, 2010)
    assert (out["draft_year"] > 2000).all() and (out["draft_year"] < 2010).all()


# ----- Integration tests (use test DB; draft table only truncated) -----


@pytest.mark.integration
def test_get_draft_table_columns_returns_table_columns():
    """get_draft_table_columns returns the list of column names in the draft table."""
    engine = get_engine(use_test=True)
    columns = get_draft_table_columns(engine)
    expected = {"player_id", "draft_year", "draft_round", "draft_pick", "team_id"}
    assert expected.issubset(set(columns)), f"Missing table columns: {expected - set(columns)}"


@pytest.mark.integration
def test_load_draft_into_test_db():
    """Load draft into test DB (after ensuring team and player exist), verify count, then truncate draft."""
    engine = get_engine(use_test=True)
    try:
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE draft CASCADE"))
            conn.commit()
        from source.load_team_data import load_teams
        from source.load_player_data import load_players
        load_teams(engine)
        load_players(engine, start_year=1990, end_year=2030)
        n = load_draft(engine, start_year=1990, end_year=2030)
        assert n > 0
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM draft"))
            count = result.scalar()
        assert count == n
    finally:
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE draft CASCADE"))
            conn.commit()
