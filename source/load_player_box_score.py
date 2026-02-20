import sys
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

# When run by path (e.g. python project/source/load_team_data.py), project root may not be on path.
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from source.db import get_engine

_data_dir = _project_root / "data"

def get_full_player_box_score_df(player_box_score_file_path: Optional[str] = None) -> pd.DataFrame:
    """Read player box score data from CSV (no DB). Used by load_player_box_score and by unit tests."""
    data_path = (
        Path(player_box_score_file_path) if player_box_score_file_path else 
        _data_dir / "player_game_logs_2020_2025.csv")
    df = pd.read_csv(data_path)
    return df

def get_player_box_score_table_columns(engine: Engine) -> list[str]:
    """Return column names of the player_box_score table (for tests)."""
    df = pd.read_sql("SELECT * FROM player_box_score LIMIT 0", engine)
    return list(df.columns)

def prepare_player_box_score_df(
    full_player_box_score_df: pd.DataFrame,
) -> pd.DataFrame:
    """Select player box score table columns, rename to DB names, and filter by game_date. Returns DataFrame ready for to_sql."""
    player_box_score = full_player_box_score_df[
        ["GAME_ID", "PLAYER_ID", "TEAM_ID", "MIN", "PTS", 
        "FGM", "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT", 
        "FTM", "FTA", "FT_PCT", "OREB", "DREB", "REB", "AST", 
        "TOV", "STL", "BLK", "BLKA", "PF", "PFD", "PLUS_MINUS"]
        ].copy()

    player_box_score.columns = [
        "game_id", "player_id", "team_id", "min_played", "pts", 
        "fgm", "fga", "fg_pct", "fg3m", "fg3a", "fg3_pct", "ftm",
        "fta", "ft_pct", "oreb", "dreb", "reb", "ast", "tov", 
        "stl", "blk", "blka", "pf", "pfd", "plus_minus"
    ]

    return player_box_score


def load_player_box_score(engine: Engine) -> int:
    """Load player box score data into the player_box_score table. Returns number of rows loaded."""
    full_player_box_score_df = get_full_player_box_score_df()
    player_box_score_df = prepare_player_box_score_df(full_player_box_score_df)

    print(f"Prepared {len(player_box_score_df)} rows for PLAYER_BOX_SCORE table")
    try:
        player_box_score_df.to_sql("player_box_score", engine, if_exists="append", index=False)
    except IntegrityError as e:
        err_msg = str(e).lower()
        if "unique" in err_msg or "duplicate" in err_msg:
            raise RuntimeError(
                "One or more player box score records already exist in the database (duplicate or constraint). "
                "Cannot append without overwriting existing data."
            ) from e
        raise
    return len(player_box_score_df)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Load player box score data into the database.")
    parser.add_argument("--test", "-t", action="store_true", help="Use test database (nba_db_test)")
    args = parser.parse_args()
    engine = get_engine(use_test=args.test)
    try:
        n = load_player_box_score(engine)
        print(f"✓ Loaded {n} rows into PLAYER_BOX_SCORE table")
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)