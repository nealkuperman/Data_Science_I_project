#!/usr/bin/env bash
# Print row counts per table (see if DB has data or only empty tables).
# Run from anywhere; uses the project directory (parent of schema/).
#
# Usage:
#   ./check_data.sh           Show counts for both DBs.
#   ./check_data.sh prod      Show counts for nba_db only.
#   ./check_data.sh test      Show counts for nba_db_test only.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

run_check() {
  local db=$1
  echo "=== $db ==="
  docker exec -i nba_postgres psql -U nba_user -d "$db" -f - < schema/check_data.sql
  echo ""
}

case "${1:-}" in
  prod)  run_check nba_db ;;
  test)  run_check nba_db_test ;;
  *)
    run_check nba_db
    run_check nba_db_test
    ;;
esac
