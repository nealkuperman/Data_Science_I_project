"""
Tests for load_team_box_score.

Unit tests: no DB, no cleanup. Run from project/:  pytest tests/test_load_team_game_log_data.py -v -m "not integration"
Integration test: uses test DB, truncates team_box_score/game/team before and after. Run from project/:  pytest tests/test_load_team_game_log_data.py -v -m integration
"""
import pandas as pd
import pytest
from sqlalchemy import text

from source.db import get_engine
from source.load_team_box_score import (
    _data_dir,
    prepare_team_box_score_df,
    load_team_box_score,
    get_full_team_box_score_df,
    get_team_box_score_table_columns,
)
from source.load_game_data import load_game_log


# ----- Unit tests (no database) -----


def test_team_box_score_csv_exists_and_has_expected_columns():
    """Team game log CSV (used for team box score) should exist and have columns needed for team_box_score table."""
    path = _data_dir / "team_game_logs_2020_2025.csv"
    assert path.exists(), f"Expected data file at {path}"
    df = pd.read_csv(path)
    required = {'GAME_ID','TEAM_ID', 'W', 'IS_HOME', 'PTS', "FGM", 
                "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT", "FTM", "FTA", "FT_PCT", 
                "OREB", "DREB", "REB", "AST", "TOV", "STL", "BLK", "BLKA", "PF", 
                "PFD"
                }
    assert required.issubset(set(df.columns)), f"Missing columns: {required - set(df.columns)}"


def test_get_full_team_box_score_df_returns_dataframe():
    """get_full_team_box_score_df() returns a DataFrame with expected columns."""
    df = get_full_team_box_score_df()
    assert isinstance(df, pd.DataFrame)
    assert "GAME_ID" in df.columns and "TEAM_ID" in df.columns and "W" in df.columns and "IS_HOME" in df.columns and "PTS" in df.columns
    assert len(df) > 0

def test_prepare_team_box_score_df_returns_team_box_score_table_shape():
    """prepare_team_box_score_df returns one row per team box score with team box score table columns."""
    # Minimal input: one game, home and away rows (IS_HOME already 1 and 0)
    full_df = pd.DataFrame([
        {"GAME_ID": "001", "TEAM_ID": 1, "W": 1, "IS_HOME": 1, "PTS": 100, "FGM": 10, "FGA": 20, "FG_PCT": 0.5, "FG3M": 3, "FG3A": 10, "FG3_PCT": 0.3, "FTM": 5, "FTA": 10, "FT_PCT": 0.5, "OREB": 2, "DREB": 3, "REB": 5, "AST": 4, "TOV": 1, "STL": 1, "BLK": 1, "BLKA": 1, "PF": 1, "PFD": 1},
        {"GAME_ID": "001", "TEAM_ID": 2, "W": 0, "IS_HOME": 0, "PTS": 98, "FGM": 10, "FGA": 20, "FG_PCT": 0.5, "FG3M": 3, "FG3A": 10, "FG3_PCT": 0.3, "FTM": 5, "FTA": 10, "FT_PCT": 0.5, "OREB": 2, "DREB": 3, "REB": 5, "AST": 4, "TOV": 1, "STL": 1, "BLK": 1, "BLKA": 1, "PF": 1, "PFD": 1},
    ])
    out = prepare_team_box_score_df(full_df)
    expected_cols = {"game_id", "team_id", "win", "is_home", "pts", "fgm", "fga", "fg_pct", "fg3m", "fg3a", "fg3_pct", "ftm", "fta", "ft_pct", "oreb", "dreb", "reb", "ast", "tov", "stl", "blk", "blka", "pf", "pfd"}
    assert set(out.columns) == expected_cols, f"Expected columns {expected_cols}, got {set(out.columns)}"
    assert len(out) == 2, "prepare_team_box_score_df returns one row per team per game (2 teams for one game)"
    assert out["game_id"].iloc[0] == "001"
    assert out["win"].iloc[0] == True
    assert out["is_home"].iloc[0] == True
    assert out["pts"].iloc[0] == 100
    assert out["fgm"].iloc[0] == 10
    assert out["fga"].iloc[0] == 20
    assert out["fg_pct"].iloc[0] == 0.5
    assert out["fg3m"].iloc[0] == 3
    assert out["fg3a"].iloc[0] == 10
    assert out["fg3_pct"].iloc[0] == 0.3
    assert out["ftm"].iloc[0] == 5
    assert out["fta"].iloc[0] == 10
    assert out["ft_pct"].iloc[0] == 0.5
    assert out["oreb"].iloc[0] == 2
    assert out["dreb"].iloc[0] == 3
    assert out["reb"].iloc[0] == 5
    assert out["ast"].iloc[0] == 4
    assert out["tov"].iloc[0] == 1
    assert out["stl"].iloc[0] == 1
    assert out["blk"].iloc[0] == 1
    assert out["blka"].iloc[0] == 1
    assert out["pf"].iloc[0] == 1
    assert out["pfd"].iloc[0] == 1

# ----- Integration tests (use test DB) -----

@pytest.mark.integration
def test_get_team_box_score_table_columns_returns_table_columns():
    """get_team_box_score_table_columns returns the list of column names in the team box score table."""
    engine = get_engine(use_test=True)
    columns = get_team_box_score_table_columns(engine)
    expected = {"team_box_id", "game_id", "team_id", "is_home", "win", "pts", "fgm", 
                "fga", "fg_pct", "fg3m", "fg3a", "fg3_pct", "ftm", "fta", "ft_pct", 
                "oreb", "dreb", "reb", "ast", "tov", "stl", "blk", "blka", "pf", "pfd"}
    assert expected.issubset(set(columns)), f"Missing table columns: {expected - set(columns)}"


@pytest.mark.integration
def test_load_team_box_score_into_test_db():
    """Load team box scores into test DB (games and teams must exist). Verify count, then truncate team box score table."""
    engine = get_engine(use_test=True)
    try:
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE team_box_score CASCADE"))
            conn.execute(text("TRUNCATE TABLE game CASCADE"))
            conn.execute(text("TRUNCATE TABLE team CASCADE"))
            conn.commit()
        from source.load_team_data import load_teams
        try:
            load_teams(engine)
        except RuntimeError as e:
            if "already exist" not in str(e).lower():
                raise
            # Teams already in DB (e.g. from another integration test); continue
        
        try:
            n = load_game_log(engine)
        except RuntimeError as e:
            if "already exist" not in str(e).lower():
                raise
            # Games already in DB (e.g. from another integration test); continue

        n = load_team_box_score(engine)
        assert n > 0
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM team_box_score"))
            count = result.scalar()
        assert count == n
    finally:
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE team_box_score CASCADE"))
            conn.execute(text("TRUNCATE TABLE game CASCADE"))
            conn.execute(text("TRUNCATE TABLE team CASCADE"))
            conn.commit()
