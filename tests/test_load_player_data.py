"""
Tests for load_player_data.

Unit tests: no DB, no cleanup. Run from project/:  pytest tests/test_load_player_data.py -v -m "not integration"
Integration test: uses test DB, truncates before and after. Run from project/:  pytest tests/test_load_player_data.py -v -m integration
"""
import pandas as pd
import pytest
from sqlalchemy import text

from source.db import get_engine
from source.load_player_data import (
    _data_dir,
    get_full_player_df,
    get_player_table_columns,
    load_players,
    prepare_player_df,
)


# ----- Unit tests (no database) -----


def test_player_csv_exists_and_has_expected_columns():
    """Player CSV should exist and have required columns for the player table."""
    path = _data_dir / "player_data_02092026.csv"
    assert path.exists(), f"Expected data file at {path}"
    df = pd.read_csv(path)
    required = {"PERSON_ID", "PLAYER_FIRST_NAME", "PLAYER_LAST_NAME", "FROM_YEAR", "POSITION", "HEIGHT", "WEIGHT", "COUNTRY"}
    assert required.issubset(set(df.columns)), f"Missing columns: {required - set(df.columns)}"


def test_get_full_player_df_returns_dataframe():
    """get_full_player_df() returns a DataFrame with expected player columns and unique player_id."""
    df = get_full_player_df()
    assert isinstance(df, pd.DataFrame)
    assert "PERSON_ID" in df.columns and "FROM_YEAR" in df.columns
    assert df["PERSON_ID"].is_unique, "PERSON_ID should be unique"
    assert len(df) > 0


def test_prepare_player_df_selects_columns_renames_and_filters_by_year():
    """prepare_player_df keeps only table columns, renames to DB names, and filters by from_year."""
    table_columns = ["player_id", "first_name", "last_name", "position", "height", "weight", "country", "from_year"]
    full_df = pd.DataFrame({
        "PERSON_ID": [1, 2, 3],
        "PLAYER_FIRST_NAME": ["A", "B", "C"],
        "PLAYER_LAST_NAME": ["X", "Y", "Z"],
        "POSITION": ["G", "F", "C"],
        "HEIGHT": ["6-0", "6-5", "6-10"],
        "WEIGHT": ["180", "200", "220"],
        "COUNTRY": ["USA", "USA", "USA"],
        "FROM_YEAR": [1995, 2002, 2010],
    })
    out = prepare_player_df(full_df, table_columns, start_year=2000, end_year=2008)
    assert set(out.columns) == set(table_columns), "output should have exactly the table columns (order may vary)"
    assert out["player_id"].tolist() == [2]  # only 2002 is in (2000, 2008)
    assert (out["from_year"] > 2000).all() and (out["from_year"] < 2008).all()


# ----- Integration tests (use test DB; truncate before and after) -----


@pytest.mark.integration
def test_get_player_table_columns_returns_table_columns():
    """get_player_table_columns returns the list of column names in the player table."""
    engine = get_engine(use_test=True)
    columns = get_player_table_columns(engine)
    expected = {"player_id", "first_name", "last_name", "position", "height", "weight", "country", "from_year"}
    assert expected.issubset(set(columns)), f"Missing table columns: {expected - set(columns)}"


@pytest.mark.integration
def test_load_players_into_test_db():
    """Load players into test DB, verify count, then truncate so test DB is clean."""
    engine = get_engine(use_test=True)
    try:
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE draft CASCADE"))
            conn.execute(text("TRUNCATE TABLE player CASCADE"))
            conn.commit()
        n = load_players(engine, start_year=1990, end_year=2030)
        assert n > 0
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM player"))
            count = result.scalar()
        assert count == n
    finally:
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE draft CASCADE"))
            conn.execute(text("TRUNCATE TABLE player CASCADE"))
            conn.commit()
