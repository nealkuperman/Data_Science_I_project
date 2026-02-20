-- NBA Database: Reset (drop all tables)
-- Run this when you want to wipe the schema and then run 01_tables.sql to recreate.
-- Order matters: drop child tables first (they reference parent tables).

-- Usage (run from terminal, or from your notebook/IDE):
--
--   Production (nba_db):
--     psql -U nba_user -d nba_db -f schema/reset_tables.sql
--
--   Test (nba_db_test):
--     psql -U nba_user -d nba_db_test -f schema/reset_tables.sql
--
--   With Docker:
--     docker exec -i nba_postgres psql -U nba_user -d nba_db_test -f - < schema/reset_tables.sql
--     (or mount the schema folder and run from inside the container)

-- =============================================================================
-- DROP ALL TABLES (reverse dependency order)
-- =============================================================================
DROP TABLE IF EXISTS player_box_score;
DROP TABLE IF EXISTS team_box_score;
DROP TABLE IF EXISTS game;
DROP TABLE IF EXISTS draft;
DROP TABLE IF EXISTS player;
DROP TABLE IF EXISTS team;
