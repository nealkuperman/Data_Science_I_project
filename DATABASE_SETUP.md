# NBA Database Setup Guide

This document explains how the PostgreSQL database is set up using Docker.

---

## Overview

We use **Docker** to run **PostgreSQL** in an isolated container. This approach:
- Keeps your Mac clean (no direct PostgreSQL installation)
- Makes the setup reproducible (anyone can run the same setup)
- Easy to start/stop/reset the database

---

## Files in This Directory

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Main configuration - tells Docker what to run |
| `init_test_db.sql` | Creates the test database on first startup (runs first) |
| `init.sql` | Runs on first startup: applies `schema/01_tables.sql` to both `nba_db` and `nba_db_test` |
| `schema/` | Table definitions (`01_tables.sql`), reset/truncate/check scripts — see **schema/README.md** |
| `NBA_DB_ER.mmd` | Entity-Relationship diagram (Mermaid format) |
| `.env` | Optional: `DATABASE_URL` and `DATABASE_TEST_URL` for the project’s Python load scripts |

---

## Understanding docker-compose.yml

```yaml
version: '3.8'

services:
  postgres:                                    # Service name
    image: postgres:16                         # Use official PostgreSQL version 16
    container_name: nba_postgres               # Name for the running container
    environment:                               # Environment variables
      POSTGRES_USER: nba_user                  # Database username
      POSTGRES_PASSWORD: nba_password         # Database password
      POSTGRES_DB: nba_db                     # Default database (created automatically)
    ports:
      - "5432:5432"                            # Map port 5432 (host:container)
    volumes:
      - nba_data:/var/lib/postgresql/data     # Persist data between restarts
      - ./init.sql:/docker-entrypoint-initdb.d/01_init.sql
      - ./init_test_db.sql:/docker-entrypoint-initdb.d/00_create_test_db.sql
    restart: unless-stopped                    # Auto-restart if it crashes

volumes:
  nba_data:                                    # Named volume for data persistence
```

### Key Concepts:

**image**: The base software to run. `postgres:16` is the official PostgreSQL image, version 16.

**environment**: Variables passed to the container. PostgreSQL uses these to configure itself.

**ports**: Maps `localhost:5432` → container's port `5432`. This lets you connect from your Mac.

**volumes**: 
- `nba_data:/var/lib/postgresql/data` - Saves database files so data survives container restarts
- `./init.sql:/docker-entrypoint-initdb.d/...` - Copies our SQL files into a special folder that PostgreSQL runs on first startup

---

## How Initialization Works

When PostgreSQL starts **for the first time**, it:

1. Creates the default database (`nba_db`) from `POSTGRES_DB` environment variable
2. Looks in `/docker-entrypoint-initdb.d/` for `.sql` files
3. Runs them in **alphabetical order**

That's why we named them:
```
00_create_test_db.sql  →  Runs first (creates nba_db_test)
01_init.sql            →  Runs second (creates tables)
```

**Important:** These scripts only run on **first startup**. If you need to re-run them, you must delete the volume (see Commands section).

---

## Databases

| Database | Purpose | When to Use |
|----------|---------|-------------|
| `nba_db` | Production | Your real data, final queries |
| `nba_db_test` | Testing | Experiments, learning, safe to break |

---

## Connection Details

| Property | Value |
|----------|-------|
| Host | `localhost` |
| Port | `5432` |
| Username | `nba_user` |
| Password | `nba_password` |
| Production DB | `nba_db` |
| Test DB | `nba_db_test` |

### Connection Strings (for Python):

```python
# Production
"postgresql://nba_user:nba_password@localhost:5432/nba_db"

# Test
"postgresql://nba_user:nba_password@localhost:5432/nba_db_test"
```

---

## Common Commands

Run these from the **project** directory (where docker-compose.yml is located).

### Start the Database

```bash
docker compose up -d
```
- `-d` = detached mode (runs in background)

### Stop the Database

```bash
docker compose down
```
- Data is preserved in the volume

### View Logs

```bash
docker compose logs -f postgres
```
- `-f` = follow (stream new logs)
- Press `Ctrl+C` to exit

### Check Status

```bash
docker compose ps
```

### Connect via Command Line

```bash
docker exec -it nba_postgres psql -U nba_user -d nba_db
```
- Opens PostgreSQL interactive shell
- Type `\q` to exit

### Reset Everything (DELETE ALL DATA)

```bash
docker compose down -v
```
- `-v` = also delete volumes (all data!)
- Next `docker compose up` will re-run init scripts

---

## Connecting from Python

### Install the driver:

```bash
pip install psycopg2-binary
```

### Basic connection:

```python
import psycopg2

# Connect to production database
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="nba_db",
    user="nba_user",
    password="nba_password"
)

# Create a cursor and run a query
cur = conn.cursor()
cur.execute("SELECT * FROM team LIMIT 5;")
rows = cur.fetchall()
print(rows)

# Always close connections
cur.close()
conn.close()
```

### Using pandas:

```python
import pandas as pd
from sqlalchemy import create_engine

# Create engine
engine = create_engine("postgresql://nba_user:nba_password@localhost:5432/nba_db")

# Read table into DataFrame
df = pd.read_sql("SELECT * FROM team", engine)

# Write DataFrame to table
df.to_sql("table_name", engine, if_exists="replace", index=False)
```

### Using the project’s load scripts

From the **project** directory, the Python loader uses `.env` in the project root for connection URLs. Create `.env` in the project directory with:

```
DATABASE_URL=postgresql://nba_user:nba_password@localhost:5432/nba_db
DATABASE_TEST_URL=postgresql://nba_user:nba_password@localhost:5432/nba_db_test
```

Then run `python -m source.load_data` (or `--test` for the test DB). See **schema/README.md** for full load options.

---

## Troubleshooting

### "Connection refused"
- Is the container running? Check with `docker compose ps`
- Start it with `docker compose up -d`

### "Database does not exist"
- The init scripts may not have run
- Reset with `docker compose down -v` then `docker compose up -d`

### "Permission denied"
- Check username/password match docker-compose.yml

### Port 5432 already in use
- Another PostgreSQL might be running
- Check with `lsof -i :5432`
- Either stop the other service or change the port in docker-compose.yml

---

## Next Steps

1. **Start the database:** `docker compose up -d` (from the project directory). On first run, init scripts create `nba_db_test` and apply the schema to both databases.
2. **If you changed the schema** (or tables already existed): run `./schema/create_tables.sh` with `-r` to reset and recreate, or see **schema/README.md** for one-DB options.
3. **Load data:** Use the notebook (`db_testing.ipynb`) or from the project directory: `python -m source.load_data` (and `--test` for the test DB). See **schema/README.md** for `--target` and other options.
4. **Check data:** From the project directory, run `./schema/check_data.sh` to see row counts per table.
