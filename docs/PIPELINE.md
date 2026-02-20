# NBA Data Pipeline: Pull → Load

## TL;DR

- **Pull:** Python + **nba_api** (you already use it in `pull_NBA_data.py`) to fetch from the NBA stats API and write CSVs.
- **Load:** Your existing `source.load_*` scripts read those CSVs and insert into Postgres.
- No extra pipeline framework is required; a small runner can chain pull + load.

---

## Why this stack

| Layer | Tool | Why |
|-------|------|-----|
| **Fetch** | **nba_api** | Official stats.nba.com API, no key for most endpoints, good coverage (game logs, rosters, draft, etc.). |
| **Transform** | **pandas** | You already use it; enough for cleaning and aligning columns to your schema. |
| **Load** | **SQLAlchemy / to_sql** | Already in your load scripts; fits Postgres and your duplicate-handling. |
| **Orchestration** | Optional: cron, `run_pipeline.py`, or notebook | Keep it simple unless you need complex scheduling. |

You don’t need Prefect/Dagster/Airflow for this unless you want to learn them or run many interdependent jobs on a schedule.

---

## Pipeline shape

Two phases keep things clear and reusable:

1. **Pull** – Fetch from nba_api → write (or overwrite) CSVs in `data/` with **fixed names** the loaders expect.
2. **Load** – Run `python -m source.load_data` (and optionally `--target`, `--test`).

Benefits:

- Re-load without re-pulling (fast).
- Re-pull without touching the DB (refresh CSVs).
- CSVs are a clear contract between pull and load; you can inspect or back them up.

---

## What the loaders expect

Your load scripts read from these paths (under `project/data/`):

| Loader | CSV (or pattern) |
|--------|-------------------|
| team | `team_info.csv` |
| player | `player_data_02092026.csv` (or pass path in code) |
| draft | same player CSV + draft logic |
| game | `team_game_logs_2020_2025.csv` |
| team_box_score | `team_game_logs_2020_2025.csv` |
| player_box_score | `player_game_logs_2020_2025.csv` |

So the pull step should write to exactly these paths (and column names) if you want “run load_data” to work without changes.

---

## Making `pull_NBA_data.py` pipeline-ready

1. **Uncomment and standardize CSV writes**  
   In `pull_NBA_data.py` you have e.g.  
   `# team_game_logs.to_csv('./data/team_game_logs_2020_2025.csv', index=False)`  
   - Use the project root so it works from any cwd, e.g.  
     `Path(__file__).resolve().parent / "data" / "team_game_logs_2020_2025.csv"`  
   - Uncomment and call `.to_csv(...)` so each fetch writes the file the corresponding loader expects.

2. **Parameterize seasons**  
   You already have `seasons_to_load`. Make it an argument (e.g. `--seasons 2020 2021 2022 2023 2024`) and build the CSV filename from that (e.g. `team_game_logs_2020_2025.csv` for 2020–2025) so one run produces the file name your loaders use.

3. **Optional: `if __name__ == "__main__"`**  
   - Call your existing functions (e.g. `getTeamGameLogs`, `getPlayerGameLogs`, `get_teams_info`, etc.) in a fixed order.  
   - Write each DataFrame to the correct `data/` path.  
   Then you can run:  
   `python pull_NBA_data.py --seasons 2020 2021 2022 2023 2024`

4. **Rate limiting**  
   Keep your `time.sleep(0.6)` (or similar) between nba_api calls to avoid blocks; the API is sensitive to heavy traffic.

---

## One command: pull then load

After pull writes the expected CSVs:

```bash
# From project directory
python pull_NBA_data.py              # or with --seasons ...
python -m source.load_data           # or --test, --target game, etc.
```

Or use the small runner (see `run_pipeline.py`): it runs pull then load so you have a single entry point.

---

## Scheduling (optional)

- **Cron (Mac/Linux):**  
  `0 6 * * * cd /path/to/project && python pull_NBA_data.py && python -m source.load_data`  
  (e.g. daily at 6 AM.)
- **Notebook:**  
  One cell that runs pull logic and writes CSVs; next cell runs `load_data.load_all(engine)`.
- **GitHub Actions:**  
  Trigger on schedule or manual dispatch; run in a job that has Python, installs deps, runs pull then load (and a DB if you want CI to hit a test DB).

---

## Summary

- **Best way to build the pipeline:** Python + **nba_api** for pull, your existing **load_data** for DB load.
- **No extra packages required** for the pipeline itself; pandas + nba_api + SQLAlchemy are enough.
- **Concrete steps:** (1) Make `pull_NBA_data.py` write CSVs to the paths and names the loaders expect; (2) Run pull, then `python -m source.load_data`; (3) Add a small `run_pipeline.py` or cron if you want one command or scheduling.
