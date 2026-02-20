-- NBA Database: Truncate all data, keep tables
-- Removes every row from every table. Tables and indexes remain.
-- Run after create_tables; safe to re-run.

-- Order: child tables first (or use CASCADE on all)
TRUNCATE TABLE player_box_score, team_box_score, game, draft, player, team CASCADE;
