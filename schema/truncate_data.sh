#!/usr/bin/env bash
# Truncate all data in both nba_db and nba_db_test (tables stay, data removed).
# Run from anywhere; uses the project directory (parent of schema/).
#
# Usage:
#   ./truncate_data.sh           Clear data in both DBs.
#   ./truncate_data.sh prod      Clear data in nba_db only.
#   ./truncate_data.sh test      Clear data in nba_db_test only.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

run_truncate() {
  local db=$1
  echo "Truncating data in $db..."
  docker exec -i nba_postgres psql -U nba_user -d "$db" -f - < schema/truncate_data.sql
}

case "${1:-}" in
  prod)  run_truncate nba_db ;;
  test)  run_truncate nba_db_test ;;
  *)
    run_truncate nba_db
    run_truncate nba_db_test
    ;;
esac

echo "Done. All data cleared; tables unchanged."
