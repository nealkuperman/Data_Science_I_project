# Summary for new chat / new env (paste this)

## Environment (uv)

- **Path:** Each project has its own `.venv` in its own folder (e.g. `Data_Science_1_project/.venv`). The folder is always `.venv`; uv doesn’t name it after the project.
- **Contents:** What’s installed (same if you use the same `pyproject.toml` + `uv.lock`).
- **Activation:** `source .venv/bin/activate`. The prompt usually shows the parent folder name (e.g. `(Data_Science_1_project)`); that “name” is from the project directory, not from uv.
- **Setup:** From project root run `uv sync` to create/update the `.venv`. Python 3.12+. Dependencies in `pyproject.toml` and `uv.lock`.

---

## Project

**What it is:** Course/portfolio project: NBA data pipeline + win prediction. Root folder: `Data_Science_1_project` (or whatever the new folder is). Uses uv for dependencies.

**Goals:** Ingest NBA data from stats.nba.com (nba_api), store in PostgreSQL (Docker), enrich with advanced stats (pace, poss), build features (rolling/expanding, diffs, rest, wins in last N), train logistic regression for win prediction. Pipeline: pull → CSV → load → DB; optional pull-then-load runner.

**Structure:**
- **source/** – `db.py` (loads `.env` from project root), load scripts: team, player, draft, game, team_box_score, player_box_score, `load_data`.
- **scripts/** – `pull_NBA_data.py`, `request_team_gamelogs.py`, `get_data_from_db.py`, `preprocessing.py`, `add_advanced_box_score_cols.py` (adds pace/poss from advanced CSV to team_box_score).
- **schema/** – PostgreSQL DDL (`01_tables.sql`), init scripts, docker-compose, shell scripts (create/check/truncate/reset).
- **tests/** – Pytest for load scripts; `conftest.py` uses test DB.
- **data/** – Gitignored; CSVs, pulled data.
- **Root:** `docker-compose.yml`, `init.sql`, `init_test_db.sql`, `DATABASE_SETUP.md`, `NBA_DB_ER.mmd`, `docs/PIPELINE.md`.

**DB:** PostgreSQL via Docker (`docker compose up -d` from project root). `.env` at project root with `DATABASE_URL` / `DATABASE_TEST_URL`; do not commit `.env`. Tables: team, player, draft, game, team_box_score, player_box_score (pace/poss on team_box_score from advanced CSV).

**Preprocessing (`scripts/preprocessing.py`):** Reads team_box_score + game (season_year, game_date, neutral_site) + opponent. Sorts by team_name, season_year, game_date. Per (team_name, season_year): game_number, days_rest, is_back_to_back, total_wins, total_losses, win_percentage, wins_last_5/10 (prior games: `shift(1).rolling(N).sum()`). Rolling and expanding averages; diff_* columns via `calc_diffs` (groupby game_id). Feature matrix X excludes `identifying_cols`; use `.loc[:, ~df.columns.isin(identifying_cols)]` for column selection (not `df[boolean_mask]`). Drop constant columns before `.corr()` (e.g. `X.loc[:, X.nunique() > 1]`). Logistic regression with optional StandardScaler, train/test split, classification report, coefficient equation.

**Conventions / gotchas:**
- Run scripts from project root so `source` and path helpers (e.g. `Path(__file__).resolve().parent.parent`) work.
- pace/poss: Only backfilled where advanced CSV has data; missing pace → diff_pace can be constant → NaN in `.corr()`; drop zero-variance or restrict to rows with pace.
- For “columns not in list” use `.loc[:, ~df.columns.isin(list)]`; plain `df[mask]` is row indexing.
- total_losses = game_number - total_wins (no extra groupby).

**New env in this folder:** `uv sync` → then `source .venv/bin/activate` or use `.venv/bin/python`.
