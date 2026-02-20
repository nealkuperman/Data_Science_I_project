#%%
import sys
from pathlib import Path
import pandas as pd

# When run by path (e.g. python project/source/load_team_data.py), project root may not be on path.
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from sqlalchemy import text
from source.db import get_engine
from scripts.get_data_from_db import *

_data_dir = _project_root / "data"

default_engine = get_engine()

# %%
query = "SELECT game_id FROM game"
game_ids_in_db = pd.read_sql(query, default_engine)

# Load advanced CSV(s). Use one file or concat if you have 2020_2025 + 2025_2026.
_csv_path = _data_dir / "team_game_logs_advanced_2020_2026.csv"

advanced_box_score = pd.read_csv(_csv_path)
missing_game_ids = set(game_ids_in_db["game_id"].unique()) - set(advanced_box_score["GAME_ID"].unique())
print(f"Game IDs in DB but not in advanced CSV: {len(missing_game_ids)}")

# %%
# CSV uses POSS (possessions); DB columns we'll add: pace, poss (snake_case).
identifier_cols = ["TEAM_ID", "GAME_ID"]
cols_to_add = ["PACE", "POSS"]  # POSS = possessions (often labeled POS in docs)
db_col_names = ["pace", "poss"]

adv = advanced_box_score[identifier_cols + cols_to_add].copy()
adv = adv.rename(columns={"GAME_ID": "game_id", "TEAM_ID": "team_id", "PACE": "pace", "POSS": "poss"})

# 2) Restrict to rows that exist in team_box_score (match on game_id, team_id).
tbs_keys = pd.read_sql("SELECT game_id, team_id FROM team_box_score", default_engine)
merge = adv.merge(tbs_keys, on=["game_id", "team_id"], how="inner")

# %%
# 1) Add columns to team_box_score if they don't exist.
with default_engine.connect() as conn:
    for col, dtype in [("pace", "DOUBLE PRECISION"), ("poss", "DOUBLE PRECISION")]:
        conn.execute(text(
            f"ALTER TABLE team_box_score ADD COLUMN IF NOT EXISTS {col} {dtype}"
        ))
    conn.commit()

# 2) Restrict to rows that exist in team_box_score (match on game_id, team_id).
tbs_keys = pd.read_sql("SELECT game_id, team_id FROM team_box_score", default_engine)
merge = adv.merge(tbs_keys, on=["game_id", "team_id"], how="inner")

# 3) Update via temp table: insert merge into temp, then UPDATE ... FROM.
merge.to_sql("_adv_update", default_engine, if_exists="replace", index=False, method="multi")
with default_engine.connect() as conn:
    conn.execute(text("""
        UPDATE team_box_score tbs
        SET pace = u.pace, poss = u.poss
        FROM _adv_update u
        WHERE tbs.game_id = u.game_id AND tbs.team_id = u.team_id
    """))
    conn.execute(text("DROP TABLE IF EXISTS _adv_update"))
    conn.commit()
print(f"Updated {len(merge)} rows with pace and poss.")
# %%
