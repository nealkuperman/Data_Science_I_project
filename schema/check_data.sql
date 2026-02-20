-- Row counts per table (quick check: data present vs empty tables)
SELECT 'team' AS table_name, COUNT(*) AS rows FROM team
UNION ALL SELECT 'player', COUNT(*) FROM player
UNION ALL SELECT 'draft', COUNT(*) FROM draft
UNION ALL SELECT 'game', COUNT(*) FROM game
UNION ALL SELECT 'team_box_score', COUNT(*) FROM team_box_score
UNION ALL SELECT 'player_box_score', COUNT(*) FROM player_box_score
ORDER BY table_name;
