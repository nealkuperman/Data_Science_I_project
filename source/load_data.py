"""
Main data load script: runs all loaders to populate the database.
Run from project root:  python -m source.load_data
Use test DB:  python -m source.load_data --test   or   python ./project/source/load_data.py --test
"""
import sys
from pathlib import Path

# When run by path (e.g. python project/source/load_data.py), project root may not be on path.
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import argparse
from typing import Optional

from source.db import get_engine
from source.load_team_data import load_teams
from source.load_player_data import load_players
from source.load_draft_data import load_draft
from source.load_game_data import load_game_log
from source.load_team_box_score import load_team_box_score
from source.load_player_box_score import load_player_box_score

def load_all(
    engine=None,
    use_test: bool = False,
    target: str = "all",
    start_year: int = 2000,
    end_year: Optional[int] = None,
):
    """Run loaders. target: 'all' | 'team' | 'player'. If a loader hits 'already exists', skip and continue. Returns dict of counts."""
    if engine is None:
        engine = get_engine(use_test=use_test)
    counts = {}

    if target in ("all", "team"):
        try:
            counts["team"] = load_teams(engine)
        except RuntimeError as e:
            if "already exist" in str(e).lower():
                print(f"Skipped team: {e}", file=sys.stderr)
                counts["team"] = 0
            else:
                raise

    if target in ("all", "player"):
        try:
            counts["player"] = load_players(engine, start_year=start_year, end_year=end_year)
        except RuntimeError as e:
            if "already exist" in str(e).lower():
                print(f"Skipped player: {e}", file=sys.stderr)
                counts["player"] = 0
            else:
                raise

    if target in ("all", "draft"):
        try:
            counts["draft"] = load_draft(engine, start_year=start_year, end_year=end_year)
        except RuntimeError as e:
            if "already exist" in str(e).lower():
                print(f"Skipped draft: {e}", file=sys.stderr)
                counts["draft"] = 0
            else:
                raise
    
    if target in ("all", "game"):
        try:
            counts["game"] = load_game_log(engine)
        except RuntimeError as e:
            if "already exist" in str(e).lower():
                print(f"Skipped game: {e}", file=sys.stderr)
                counts["game"] = 0
            else:
                raise
        
    if target in ("all", "team_box_score"):
        try:
            counts["team_box_score"] = load_team_box_score(engine)
        except RuntimeError as e:
            if "already exist" in str(e).lower():
                print(f"Skipped team box score: {e}", file=sys.stderr)
                counts["team_box_score"] = 0
            else:
                raise

    
    if target in ("all", "player_box_score"):
        try:
            counts["player_box_score"] = load_player_box_score(engine)
        except RuntimeError as e:
            if "already exist" in str(e).lower():
                print(f"Skipped player box score: {e}", file=sys.stderr)
                counts["player_box_score"] = 0
            else:
                raise
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load NBA data into the database.")
    parser.add_argument("--test", "-t", action="store_true", help="Use test database (nba_db_test)")
    parser.add_argument("--target", choices=("all", "team", "player", "draft", "game", "team_box_score", "player_box_score"), default="all", help="What to load (default: all)")
    parser.add_argument("--start_year", "-s", type=int, default=2000, help="Player data: from_year > this (default 2000)")
    parser.add_argument("--end_year", "-e", type=int, default=None, help="Player data: from_year < this (optional)")
    args = parser.parse_args()
    engine = get_engine(use_test=args.test)
    counts = load_all(engine, target=args.target, start_year=args.start_year, end_year=args.end_year)
    for table, n in counts.items():
        print(f"✓ Loaded {n} rows into {table}")
    print("Done.")
