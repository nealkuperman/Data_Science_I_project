"""
Tests for load_player_box_score.

Unit tests: no DB, no cleanup. Run from project/:  pytest tests/test_load_player_box_score_data.py -v -m "not integration"
Integration test: uses test DB, truncates player_box_score/game/player/team before and after. Run from project/:  pytest tests/test_load_player_box_score_data.py -v -m integration
"""
import pandas as pd
import pytest
from sqlalchemy import text

from source.db import get_engine
from source.load_player_box_score import (
    _data_dir,
    prepare_player_box_score_df,
    load_player_box_score,
    get_full_player_box_score_df,
    get_player_box_score_table_columns,
)
from source.load_game_data import load_game_log
from source.load_player_data import load_players
from source.load_team_data import load_teams
# ----- Unit tests (no database) -----


def test_player_box_score_csv_exists_and_has_expected_columns():
    """Player game log CSV (used for player box score) should exist and have columns needed for player_box_score table."""
    path = _data_dir / "player_game_logs_2020_2025.csv"
    assert path.exists(), f"Expected data file at {path}"
    df = pd.read_csv(path)
    required = {'GAME_ID','PLAYER_ID', 'TEAM_ID', 'MIN', 'PTS', "FGM", 
                "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT", "FTM", "FTA", "FT_PCT", 
                "OREB", "DREB", "REB", "AST", "TOV", "STL", "BLK", "BLKA", "PF", 
                "PFD", "PLUS_MINUS"
                }
    assert required.issubset(set(df.columns)), f"Missing columns: {required - set(df.columns)}"


def test_get_full_player_box_score_df_returns_dataframe():
    """get_full_player_box_score_df() returns a DataFrame with expected columns."""
    df = get_full_player_box_score_df()
    assert isinstance(df, pd.DataFrame)
    assert "GAME_ID" in df.columns and "PLAYER_ID" in df.columns and "TEAM_ID" in df.columns and "MIN" in df.columns and "PTS" in df.columns
    assert len(df) > 0

def test_prepare_player_box_score_df_returns_player_box_score_table_shape():
    """prepare_player_box_score_df returns one row per player per game with player box score table columns."""
    # Minimal input: one game, two players (UNIQUE (game_id, player_id) in schema)
    full_df = pd.DataFrame([
        {"GAME_ID": "001", "PLAYER_ID": 1, "TEAM_ID": 1, "MIN": 10, "PTS": 100, "FGM": 10, "FGA": 20, "FG_PCT": 0.5, "FG3M": 3, "FG3A": 10, "FG3_PCT": 0.3, "FTM": 5, "FTA": 10, "FT_PCT": 0.5, "OREB": 2, "DREB": 3, "REB": 5, "AST": 4, "TOV": 1, "STL": 1, "BLK": 1, "BLKA": 1, "PF": 1, "PFD": 1, "PLUS_MINUS": 1},
        {"GAME_ID": "001", "PLAYER_ID": 2, "TEAM_ID": 1, "MIN": 10, "PTS": 98, "FGM": 10, "FGA": 20, "FG_PCT": 0.5, "FG3M": 3, "FG3A": 10, "FG3_PCT": 0.3, "FTM": 5, "FTA": 10, "FT_PCT": 0.5, "OREB": 2, "DREB": 3, "REB": 5, "AST": 4, "TOV": 1, "STL": 1, "BLK": 1, "BLKA": 1, "PF": 1, "PFD": 1, "PLUS_MINUS": -1},
    ])
    out = prepare_player_box_score_df(full_df)
    expected_cols = {"game_id", "player_id", "team_id", "min_played", "pts", "fgm", "fga", "fg_pct", "fg3m", "fg3a", "fg3_pct", "ftm", "fta", "ft_pct", "oreb", "dreb", "reb", "ast", "tov", "stl", "blk", "blka", "pf", "pfd", "plus_minus"}
    assert set(out.columns) == expected_cols, f"Expected columns {expected_cols}, got {set(out.columns)}"
    assert len(out) == 2, "prepare_player_box_score_df returns one row per player per game (2 players in one game)"
    assert out["game_id"].iloc[0] == "001"
    assert out["player_id"].iloc[0] == 1
    assert out["team_id"].iloc[0] == 1
    assert out["min_played"].iloc[0] == 10
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
    assert out["plus_minus"].iloc[0] == 1

# ----- Integration tests (use test DB) -----

@pytest.mark.integration
def test_get_player_box_score_table_columns_returns_table_columns():
    """get_player_box_score_table_columns returns the list of column names in the player box score table."""
    engine = get_engine(use_test=True)
    columns = get_player_box_score_table_columns(engine)
    expected = {"player_box_id", "game_id", "player_id", "team_id", "min_played", "pts", "fgm", 
                "fga", "fg_pct", "fg3m", "fg3a", "fg3_pct", "ftm", "fta", "ft_pct", 
                "oreb", "dreb", "reb", "ast", "tov", "stl", "blk", "blka", "pf", "pfd", "plus_minus"}
    assert expected.issubset(set(columns)), f"Missing table columns: {expected - set(columns)}"


@pytest.mark.integration
def test_load_player_box_score_into_test_db():
    """Load player box scores into test DB (games and players must exist). Verify count, then truncate player box score table."""
    engine = get_engine(use_test=True)
    try:
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE player_box_score CASCADE"))
            conn.execute(text("TRUNCATE TABLE game CASCADE"))
            conn.execute(text("TRUNCATE TABLE player CASCADE"))
            conn.execute(text("TRUNCATE TABLE team CASCADE"))
            conn.commit()
        try:
            load_players(engine)
            load_teams(engine)
        except RuntimeError as e:
            if "already exist" not in str(e).lower():
                raise
            # Players already in DB (e.g. from another integration test); continue
        
        try:
            n = load_game_log(engine)
        except RuntimeError as e:
            if "already exist" not in str(e).lower():
                raise
            # Games already in DB (e.g. from another integration test); continue

        n = load_player_box_score(engine)
        assert n > 0
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM player_box_score"))
            count = result.scalar()
        assert count == n
    finally:
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE player_box_score CASCADE"))
            conn.execute(text("TRUNCATE TABLE game CASCADE"))
            conn.execute(text("TRUNCATE TABLE player CASCADE"))
            conn.execute(text("TRUNCATE TABLE team CASCADE"))
            conn.commit()
