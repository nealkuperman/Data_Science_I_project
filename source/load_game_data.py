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

# Full mapping for game-log CSV; prepare_game_log_df builds game table rows from home/away split.
column_naming_conversion = {
    'SEASON_YEAR': 'season_year',
    'TEAM_ID': 'team_id',
    'TEAM_ABBREVIATION': 'team_abbreviation',
    'TEAM_NAME': 'team_name',
    'GAME_ID': 'game_id',
    'GAME_DATE': 'game_date',
    'MATCHUP': 'matchup',
    'WL': 'wl',
    'MIN': 'min',
    'FGM': 'fgm',
    'FGA': 'fga',
    'FG_PCT': 'fg_pct',
    'FG3M': 'fg3m',
    'FG3A': 'fg3a',
    'FG3_PCT': 'fg3_pct',
    'FTM': 'ftm',
    'FTA': 'fta',
    'FT_PCT': 'ft_pct',
    'OREB': 'oreb',
    'DREB': 'dreb',
    'REB': 'reb',
    'AST': 'ast',
    'TOV': 'tov',
    'STL': 'stl',
    'BLK': 'blk',
    'BLKA': 'blka',
    'PF': 'pf',
    'PFD': 'pfd',
    'PTS': 'pts',
    'PLUS_MINUS': 'plus_minus',
    'GP_RANK': 'gp_rank',
    'W_RANK': 'w_rank',
    'L_RANK': 'l_rank',
    'W_PCT_RANK': 'w_pct_rank',
    'MIN_RANK': 'min_rank',
    'FGM_RANK': 'fgm_rank',
    'FGA_RANK': 'fga_rank',
    'FG_PCT_RANK': 'fg_pct_rank',
    'FG3M_RANK': 'fg3m_rank',
    'FG3A_RANK': 'fg3a_rank',
    'FG3_PCT_RANK': 'fg3_pct_rank',
    'FTM_RANK': 'ftm_rank',
    'FTA_RANK': 'fta_rank',
    'FT_PCT_RANK': 'ft_pct_rank',
    'OREB_RANK': 'oreb_rank',
    'DREB_RANK': 'dreb_rank',
    'REB_RANK': 'reb_rank',
    'AST_RANK': 'ast_rank',
    'TOV_RANK': 'tov_rank',
    'STL_RANK': 'stl_rank',
    'BLK_RANK': 'blk_rank',
    'BLKA_RANK': 'blka_rank',
    'PF_RANK': 'pf_rank',
    'PFD_RANK': 'pfd_rank',
    'PTS_RANK': 'pts_rank',
    'PLUS_MINUS_RANK': 'plus_minus_rank',
    'AVAILABLE_FLAG': 'available_flag',
    'W': 'w',
    'IS_HOME': 'is_home',
    'NEUTRAL_SITE': 'neutral_site'
}

def get_full_game_log_df(game_log_file_path: Optional[str] = None) -> pd.DataFrame:
    """Read game log data from CSV (no DB). Used by load_game_logs and by unit tests."""
    data_path = Path(game_log_file_path) if game_log_file_path else _data_dir / "team_game_logs_2020_2025.csv"
    df = pd.read_csv(data_path)
    return df

def get_game_log_table_columns(engine: Engine) -> list[str]:
    df = pd.read_sql("SELECT * FROM game LIMIT 0", engine)  # no rows, just structure
    return list(df.columns)

def fix_neutral_site_home(team_game_log_df):
    # Handle games at a neutral site. The original data has both teams listed as away
    # We will set the team with the lower team_id as the home team and create
    # a new column neutral_site to denote if the game was played at a neutral site
    # (1 if neutral, 0 if not)

    df = team_game_log_df.copy()
    neutral_game_ids = (
        df.groupby('GAME_ID')['IS_HOME'].sum()
        .loc[lambda s: s == 0]
        .index
    )

    mask = df['GAME_ID'].isin(neutral_game_ids)

    df.loc[mask, 'IS_HOME'] = (
        df.loc[mask]
        .groupby('GAME_ID')['TEAM_ID']
        .transform(lambda x: (x == x.min()).astype(int))
    )

    df['NEUTRAL_SITE'] = df['GAME_ID'].isin(neutral_game_ids).astype(int)

    per_game = df.groupby('GAME_ID')['IS_HOME'].sum()
    assert (per_game == 1).all(), "Some games don't have exactly one home team"
    print(f"✓ All {len(per_game)} games have exactly one home and one away")
    print(f"✓ Neutral-site games: {df['NEUTRAL_SITE'].sum() // 2}")  # divide by 2 (two rows per game)

    return df


def prepare_game_log_df(
    full_game_log_df: pd.DataFrame,
) -> pd.DataFrame:
    """Select game table columns, rename to DB names, and filter by game_date. Returns DataFrame ready for to_sql."""
    
    # Fix neutral site home
    full_game_log_df = fix_neutral_site_home(full_game_log_df)
    
    # Split into home and away
    home_games = full_game_log_df[full_game_log_df['IS_HOME'] == 1][
        ['GAME_ID', 'GAME_DATE', 'SEASON_YEAR', 'MIN','TEAM_ID', 'PTS']
    ].copy()
    home_games.columns = ['game_id', 'game_date', 'season_year', 'minutes_played', 'home_team_id', 'home_score']
    home_games["minutes_played"] = round(home_games["minutes_played"]).astype(int)
    away_games = full_game_log_df[full_game_log_df['IS_HOME'] == 0][
        ['GAME_ID', 'TEAM_ID', 'PTS']
    ].copy()
    away_games.columns = ['game_id', 'away_team_id', 'away_score']

    game_df = home_games.merge(away_games, on='game_id')

    # Number of overtime periods (game table has CHECK (overtime >= 0))
    ot = (game_df["minutes_played"] - 48) / 5
    game_df["overtime"] = ot.clip(lower=0).astype(int)

    # Add neutral_site column
    neutral = full_game_log_df[full_game_log_df['IS_HOME'] == 1][['GAME_ID','NEUTRAL_SITE']]
    neutral = neutral.rename(columns={'GAME_ID': 'game_id', 'NEUTRAL_SITE': 'neutral_site'})
    game_df = game_df.merge(neutral, on='game_id', how='left')

    return game_df


def load_game_log(engine: Engine) -> int:
    """Load game data into the game table. Returns number of rows loaded."""
    full_game_log_df = get_full_game_log_df()
    game_log_df = prepare_game_log_df(full_game_log_df)

    print(f"Prepared {len(game_log_df)} rows for GAME table")
    try:
        game_log_df.to_sql("game", engine, if_exists="append", index=False)
    except IntegrityError as e:
        err_msg = str(e).lower()
        if "unique" in err_msg or "duplicate" in err_msg:
            raise RuntimeError(
                "One or more game log records already exist in the database (duplicate or constraint). "
                "Cannot append without overwriting existing data."
            ) from e
        raise
    return len(game_log_df)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Load game data into the database.")
    parser.add_argument("--test", "-t", action="store_true", help="Use test database (nba_db_test)")
    args = parser.parse_args()
    engine = get_engine(use_test=args.test)
    try:
        n = load_game_log(engine)
        print(f"✓ Loaded {n} rows into GAME table")
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)