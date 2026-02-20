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

column_naming_conversion = {
    'PERSON_ID': 'player_id',
    'PLAYER_LAST_NAME': 'last_name',
    'PLAYER_FIRST_NAME': 'first_name',
    'PLAYER_SLUG': 'player_slug',
    'TEAM_ID': 'team_id',
    'TEAM_SLUG': 'team_slug',
    'IS_DEFUNCT': 'is_defunct',
    'TEAM_CITY': 'team_city',
    'TEAM_NAME': 'team_name',
    'TEAM_ABBREVIATION': 'team_abbreviation',
    'JERSEY_NUMBER': 'jersey_number',
    'POSITION': 'position',
    'HEIGHT': 'height',
    'WEIGHT': 'weight',
    'COLLEGE': 'college',
    'COUNTRY': 'country',
    'DRAFT_YEAR': 'draft_year',
    'DRAFT_ROUND': 'draft_round',
    'DRAFT_NUMBER': 'draft_number',
    'ROSTER_STATUS': 'roster_status',
    'PTS': 'pts',
    'REB': 'reb',
    'AST': 'ast',
    'STATS_TIMEFRAME': 'stats_timeframe',
    'FROM_YEAR': 'from_year',
    'TO_YEAR': 'to_year'
}

def get_full_player_df(player_file_path: Optional[str] = None) -> pd.DataFrame:
    """Read player data from CSV (no DB). Used by load_players and by unit tests."""
    data_path = Path(player_file_path) if player_file_path else _data_dir / "player_data_02092026.csv"
    df = pd.read_csv(data_path)
    return df


def get_player_table_columns(engine: Engine) -> list[str]:
    df = pd.read_sql("SELECT * FROM player LIMIT 0", engine)  # no rows, just structure
    return list(df.columns)


def prepare_player_df(
    full_player_df: pd.DataFrame,
    player_table_columns: list[str],
    start_year: int = 2000,
    end_year: Optional[int] = None,
) -> pd.DataFrame:
    """Select table columns, rename to DB names, and filter by from_year. Returns DataFrame ready for to_sql."""
    original_columns = [
        key for key, value in column_naming_conversion.items()
        if value in player_table_columns
    ]
    player_df = full_player_df[original_columns].copy()
    player_df.columns = [column_naming_conversion[col] for col in player_df.columns]
    player_df = player_df[player_df["from_year"] > start_year]
    if end_year is not None:
        player_df = player_df[player_df["from_year"] < end_year]
    return player_df


def load_players(engine: Engine, start_year: int = 2000, end_year: Optional[int] = None) -> int:
    """Load player data into the player table. Returns number of rows loaded."""
    full_player_df = get_full_player_df()
    player_table_columns = get_player_table_columns(engine)
    player_df = prepare_player_df(full_player_df, player_table_columns, start_year, end_year)
    print(f"Prepared {len(player_df)} players into PLAYER table")
    try:
        player_df.to_sql("player", engine, if_exists="append", index=False)
    except IntegrityError as e:
        err_msg = str(e).lower()
        if "unique" in err_msg or "duplicate" in err_msg:
            raise RuntimeError(
                "One or more players already exist in the database (duplicate player_id). "
                "Cannot append without overwriting existing data."
            ) from e
        raise
    return len(player_df)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Load player data into the database.")
    parser.add_argument("--test", "-t", action="store_true", help="Use test database (nba_db_test)")
    parser.add_argument("--start_year", "-s", type=int, default=2000, help="Start year for player data")
    parser.add_argument("--end_year", "-e", type=int, help="End year for player data")
    args = parser.parse_args()
    engine = get_engine(use_test=args.test)
    try:
        n = load_players(engine, start_year=args.start_year, end_year=args.end_year)
        print(f"✓ Loaded {n} players into PLAYER table")
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)