"""
Tests for load_game_data.

Unit tests: no DB, no cleanup. Run from project/:  pytest tests/test_load_game_data.py -v -m "not integration"
Integration test: uses test DB, truncates game before and after. Run from project/:  pytest tests/test_load_game_data.py -v -m integration
"""
import pandas as pd
import pytest
from sqlalchemy import text

from source.db import get_engine
from source.load_game_data import (
    _data_dir,
    fix_neutral_site_home,
    get_full_game_log_df,
    get_game_log_table_columns,
    load_game_log,
    prepare_game_log_df,
)


# ----- Unit tests (no database) -----


def test_game_log_csv_exists_and_has_expected_columns():
    """Game log CSV should exist and have columns needed for game table."""
    path = _data_dir / "team_game_logs_2020_2025.csv"
    assert path.exists(), f"Expected data file at {path}"
    df = pd.read_csv(path)
    required = {"GAME_ID", "GAME_DATE", "SEASON_YEAR", "MIN", "TEAM_ID", "PTS", "IS_HOME"}
    assert required.issubset(set(df.columns)), f"Missing columns: {required - set(df.columns)}"


def test_get_full_game_log_df_returns_dataframe():
    """get_full_game_log_df() returns a DataFrame with expected columns."""
    df = get_full_game_log_df()
    assert isinstance(df, pd.DataFrame)
    assert "GAME_ID" in df.columns and "IS_HOME" in df.columns and "PTS" in df.columns
    assert len(df) > 0


def test_prepare_game_log_df_returns_game_table_shape():
    """prepare_game_log_df returns one row per game with game table columns."""
    # Minimal input: one game, home and away rows (IS_HOME already 1 and 0)
    full_df = pd.DataFrame([
        {"GAME_ID": "001", "GAME_DATE": "2024-01-15", "SEASON_YEAR": "2023-24", "MIN": 48, "TEAM_ID": 1, "PTS": 100, "IS_HOME": 1},
        {"GAME_ID": "001", "GAME_DATE": "2024-01-15", "SEASON_YEAR": "2023-24", "MIN": 48, "TEAM_ID": 2, "PTS": 98, "IS_HOME": 0},
    ])
    out = prepare_game_log_df(full_df)
    expected_cols = {"game_id", "game_date", "season_year", "minutes_played", "home_team_id", "away_team_id", "home_score", "away_score", "overtime", "neutral_site"}
    assert set(out.columns) == expected_cols, f"Expected columns {expected_cols}, got {set(out.columns)}"
    assert len(out) == 1
    assert out["game_id"].iloc[0] == "001"
    assert out["overtime"].iloc[0] >= 0


def test_fix_neutral_site_home_ensures_one_home_per_game():
    """fix_neutral_site_home adds NEUTRAL_SITE and ensures exactly one home per game."""
    # Two games: one normal (1 home, 1 away), one neutral (both away -> fix assigns lower team_id as home)
    df = pd.DataFrame([
        {"GAME_ID": "g1", "TEAM_ID": 10, "IS_HOME": 1},
        {"GAME_ID": "g1", "TEAM_ID": 20, "IS_HOME": 0},
        {"GAME_ID": "g2", "TEAM_ID": 30, "IS_HOME": 0},
        {"GAME_ID": "g2", "TEAM_ID": 40, "IS_HOME": 0},
    ])
    out = fix_neutral_site_home(df)
    assert "NEUTRAL_SITE" in out.columns
    per_game = out.groupby("GAME_ID")["IS_HOME"].sum()
    assert (per_game == 1).all()


# ----- Integration tests (use test DB) -----


@pytest.mark.integration
def test_get_game_log_table_columns_returns_table_columns():
    """get_game_log_table_columns returns the list of column names in the game table."""
    engine = get_engine(use_test=True)
    columns = get_game_log_table_columns(engine)
    expected = {"game_id", "game_date", "season_year", "minutes_played", "home_team_id", "away_team_id", "home_score", "away_score", "overtime", "neutral_site"}
    assert expected.issubset(set(columns)), f"Missing table columns: {expected - set(columns)}"


@pytest.mark.integration
def test_load_game_log_into_test_db():
    """Load games into test DB (teams must exist). Verify count, then truncate game table."""
    engine = get_engine(use_test=True)
    try:
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE team_box_score CASCADE"))
            conn.execute(text("TRUNCATE TABLE player_box_score CASCADE"))
            conn.execute(text("TRUNCATE TABLE game CASCADE"))
            conn.commit()
        from source.load_team_data import load_teams
        try:
            load_teams(engine)
        except RuntimeError as e:
            if "already exist" not in str(e).lower():
                raise
            # Teams already in DB (e.g. from another integration test); continue
        n = load_game_log(engine)
        assert n > 0
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM game"))
            count = result.scalar()
        assert count == n
    finally:
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE team_box_score CASCADE"))
            conn.execute(text("TRUNCATE TABLE player_box_score CASCADE"))
            conn.execute(text("TRUNCATE TABLE game CASCADE"))
            conn.commit()
