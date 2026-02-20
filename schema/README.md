# NBA Database Schema

This folder contains the SQL definitions for the NBA database tables, scripts to apply them, and utilities to manage data in the Docker Postgres container.

## Files

| File | Purpose |
|------|---------|
| `01_tables.sql` | Creates all tables and indexes. Does not drop anything. |
| `reset_tables.sql` | Drops all tables (use when you want a clean slate before re-running `01_tables.sql`). |
| `create_tables.sh` | Runs `01_tables.sql` against both DBs; optional `-r` / `--reset` runs `reset_tables.sql` first. |
| `truncate_data.sql` | Removes all rows from all tables; tables and structure are kept. |
| `truncate_data.sh` | Runs `truncate_data.sql` on one or both DBs. Args: none (both), `prod`, or `test`. |
| `check_data.sql` | Prints row counts per table (quick check: data present vs empty). |
| `check_data.sh` | Runs `check_data.sql` on one or both DBs. Args: none (both), `prod`, or `test`. |

## Prerequisites

- Docker Desktop running
- NBA Postgres container up: from the **project** directory, run `docker compose up -d`
- All commands below are run from the **project** directory (parent of `schema/`), unless noted.

## Shell scripts (recommended)

The `.sh` scripts can be run from anywhere; they resolve the project directory from the script path. From the project directory or `project/schema/`:

| Script | Usage |
|--------|--------|
| **Create tables** | `./schema/create_tables.sh` — both DBs. Add `-r` or `--reset` to drop tables first, then create. |
| **Truncate data** | `./schema/truncate_data.sh` — clear all data, keep tables. Use `prod` or `test` for one DB. |
| **Check row counts** | `./schema/check_data.sh` — show rows per table. Use `prod` or `test` for one DB. |

## Set up the databases

### Option 1: Fresh create (no existing tables, or you don’t care about existing data)

Run the schema against both production and test:

```bash
# Production (nba_db)
docker exec -i nba_postgres psql -U nba_user -d nba_db -f - < schema/01_tables.sql

# Test (nba_db_test)
docker exec -i nba_postgres psql -U nba_user -d nba_db_test -f - < schema/01_tables.sql
```

One-liner for both:

```bash
docker exec -i nba_postgres psql -U nba_user -d nba_db -f - < schema/01_tables.sql && \
docker exec -i nba_postgres psql -U nba_user -d nba_db_test -f - < schema/01_tables.sql
```

### Option 2: Reset then create (wipe existing tables, then recreate)

If tables already exist and you want to start over:

```bash
# Reset production
docker exec -i nba_postgres psql -U nba_user -d nba_db -f - < schema/reset_tables.sql

# Reset test
docker exec -i nba_postgres psql -U nba_user -d nba_db_test -f - < schema/reset_tables.sql

# Create tables in production
docker exec -i nba_postgres psql -U nba_user -d nba_db -f - < schema/01_tables.sql

# Create tables in test
docker exec -i nba_postgres psql -U nba_user -d nba_db_test -f - < schema/01_tables.sql
```

## Verify

List tables in each database:

```bash
docker exec -it nba_postgres psql -U nba_user -d nba_db -c "\dt"
docker exec -it nba_postgres psql -U nba_user -d nba_db_test -c "\dt"
```

You should see: `draft`, `game`, `player`, `player_box_score`, `team`, `team_box_score`.

## Command reference

| Goal | Command |
|------|--------|
| Create tables (both DBs) | `./schema/create_tables.sh` — or with `-r` to reset first |
| Truncate data (clear rows, keep tables) | `./schema/truncate_data.sh` — or `prod` / `test` for one DB |
| Check row counts | `./schema/check_data.sh` — or `prod` / `test` for one DB |
| Reset one DB (drop tables) | `docker exec -i nba_postgres psql -U nba_user -d <nba_db or nba_db_test> -f - < schema/reset_tables.sql` |
| Create tables in one DB | `docker exec -i nba_postgres psql -U nba_user -d <nba_db or nba_db_test> -f - < schema/01_tables.sql` |
| Truncate one DB (SQL only) | `docker exec -i nba_postgres psql -U nba_user -d <nba_db or nba_db_test> -f - < schema/truncate_data.sql` |
| List tables | `docker exec -it nba_postgres psql -U nba_user -d <nba_db or nba_db_test> -c "\dt"` |
| Interactive psql | `docker exec -it nba_postgres psql -U nba_user -d nba_db` (then `\dt`, `\q`, etc.) |

## After schema is applied

Load data from your notebook (`db_testing.ipynb`) or from the project’s Python loader. From the **project** directory:

```bash
python -m source.load_data              # load all tables into nba_db
python -m source.load_data --test      # load all tables into nba_db_test
```

Use `--target team`, `player`, `draft`, `game`, `team_box_score`, or `player_box_score` to load a single table. The notebook connects to `nba_db` by default; switch to `nba_db_test` in the connection string to use the test database.
