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

# Full mapping for team box score CSV; prepare_team_box_score_df builds team box score table rows.
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

def get_full_team_box_score_df(team_box_score_file_path: Optional[str] = None) -> pd.DataFrame:
    """Read team box score data from CSV (no DB). Used by load_team_box_score and by unit tests."""
    data_path = (
        Path(team_box_score_file_path) if team_box_score_file_path else 
        _data_dir / "team_game_logs_2020_2025.csv")
    df = pd.read_csv(data_path)
    return df

def get_team_box_score_table_columns(engine: Engine) -> list[str]:
    """Return column names of the team_box_score table (for tests)."""
    df = pd.read_sql("SELECT * FROM team_box_score LIMIT 0", engine)
    return list(df.columns)

def prepare_team_box_score_df(
    full_team_box_score_df: pd.DataFrame,
) -> pd.DataFrame:
    """Select team box score table columns, rename to DB names, and filter by game_date. Returns DataFrame ready for to_sql."""
    team_box_score = full_team_box_score_df[
        ['GAME_ID','TEAM_ID', 'W', 'IS_HOME', 'PTS', "FGM", 
        "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT", "FTM", "FTA", "FT_PCT", 
        "OREB", "DREB", "REB", "AST", "TOV", "STL", "BLK", "BLKA", "PF", 
        "PFD"]
        ].copy()

    team_box_score.columns = [
        'game_id', 'team_id', 'win', 'is_home', 'pts', 'fgm', 
        'fga', 'fg_pct', 'fg3m', 'fg3a', 'fg3_pct', 'ftm', 'fta', 'ft_pct', 
        'oreb', 'dreb', 'reb', 'ast', 'tov', 'stl', 'blk', 'blka', 'pf', 'pfd'
    ]

    # Convert win and is_home from 1/0 to boolean
    team_box_score['win'] = team_box_score['win'].astype(bool)
    team_box_score['is_home'] = team_box_score['is_home'].astype(bool)
    
    return team_box_score


def load_team_box_score(engine: Engine) -> int:
    """Load team box score data into the team_box_score table. Returns number of rows loaded."""
    full_team_box_score_df = get_full_team_box_score_df()
    team_box_score_df = prepare_team_box_score_df(full_team_box_score_df)

    print(f"Prepared {len(team_box_score_df)} rows for TEAM_BOX_SCORE table")
    try:
        team_box_score_df.to_sql("team_box_score", engine, if_exists="append", index=False)
    except IntegrityError as e:
        err_msg = str(e).lower()
        if "unique" in err_msg or "duplicate" in err_msg:
            raise RuntimeError(
                "One or more team box score records already exist in the database (duplicate or constraint). "
                "Cannot append without overwriting existing data."
            ) from e
        raise
    return len(team_box_score_df)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Load team box score data into the database.")
    parser.add_argument("--test", "-t", action="store_true", help="Use test database (nba_db_test)")
    args = parser.parse_args()
    engine = get_engine(use_test=args.test)
    try:
        n = load_team_box_score(engine)
        print(f"✓ Loaded {n} rows into TEAM_BOX_SCORE table")
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)