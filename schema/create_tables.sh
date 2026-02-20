#!/usr/bin/env bash
# Create tables in both nba_db and nba_db_test by running 01_tables.sql.
# Run from anywhere; the script will use the project directory (parent of schema/).
#
# Usage:
#   ./create_tables.sh           Create tables only (fails if tables already exist).
#   ./create_tables.sh -r        Reset both DBs (drop tables), then create tables.
#   ./create_tables.sh --reset   Same as -r.

set -e
RESET=false
for arg in "$@"; do
  case "$arg" in
    -r|--reset) RESET=true ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "Using directory: $PROJECT_DIR"

if [ "$RESET" = true ]; then
  echo "Resetting nba_db (production)..."
  docker exec -i nba_postgres psql -U nba_user -d nba_db -f - < schema/reset_tables.sql
  echo "Resetting nba_db_test (test)..."
  docker exec -i nba_postgres psql -U nba_user -d nba_db_test -f - < schema/reset_tables.sql
  echo "Reset done. Creating tables..."
fi

echo "Creating tables in nba_db (production)..."
docker exec -i nba_postgres psql -U nba_user -d nba_db -f - < schema/01_tables.sql
echo "Creating tables in nba_db_test (test)..."
docker exec -i nba_postgres psql -U nba_user -d nba_db_test -f - < schema/01_tables.sql
echo "Done. Tables created in both databases."
