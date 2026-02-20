import sys
from pathlib import Path

import pandas as pd
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

# When run by path (e.g. python project/source/load_team_data.py), project root may not be on path.
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from source.db import get_engine

_data_dir = _project_root / "data"


def get_team_df() -> pd.DataFrame:
    """Read and prepare team data from CSV (no DB). Used by load_teams and by unit tests."""
    df = pd.read_csv(_data_dir / "team_info.csv")
    df.columns = df.columns.str.lower()
    return df


def load_teams(engine: Engine) -> int:
    """Load team_info.csv into the team table. Returns number of rows loaded."""
    team_df = get_team_df()
    try:
        team_df.to_sql("team", engine, if_exists="append", index=False)
    except IntegrityError as e:
        err_msg = str(e).lower()
        if "unique" in err_msg or "duplicate" in err_msg:
            raise RuntimeError(
                "One or more teams already exist in the database (duplicate team_id). "
                "Cannot append without overwriting existing data."
            ) from e
        raise
    return len(team_df)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Load team data into the database.")
    parser.add_argument("--test", "-t", action="store_true", help="Use test database (nba_db_test)")
    args = parser.parse_args()
    engine = get_engine(use_test=args.test)
    try:
        n = load_teams(engine)
        print(f"✓ Loaded {n} teams")
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)