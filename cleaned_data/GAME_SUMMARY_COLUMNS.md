# Final game summary: column reference

This document describes every column in the **final game summary** DataFrame produced by `preprocessing.py` (after the main pipeline: query → sort → game/days-rest/wins → diffs → rolling/expanding averages). All rolling and expanding stats are computed **per (team_name, season_year)** in game-date order.

**Conventions used below**

- **diff_*** = for this row’s team, **this team’s value minus the opponent’s value** for that same game (one row per team per game, so each row gets its own differential).
- ***_rolling_mean_prev_5** = mean over the **5 games before** the current game (current game excluded); uses a shifted series so it is “prior games only.”
- ***_average** = **expanding mean** from the start of the season through the current game (including the current game).
- **win_percentage_last_5 / last_10** = wins in the last 5/10 prior games ÷ 5 or 10 (denominator is always 5 or 10 even when fewer games have been played).

---

## Identifiers and game context

| Column | Description |
|--------|--------------|
| **team_name** | Name of the team this row describes. |
| **opponent_name** | Name of the opposing team in this game. |
| **opponent_pts** | Points scored by the opponent in this game. |
| **team_box_id** | Primary key of the `team_box_score` row (DB). |
| **game_id** | Unique game identifier (DB). |
| **team_id** | Team identifier (DB). |
| **is_home** | Whether this team was the home team (Boolean or 0/1). |
| **season_year** | Season label (e.g. `"2020-21"`). |
| **game_date** | Date of the game. |
| **minutes_played** | Game length in minutes (from `game` table; exact definition—e.g. regulation only or including OT—depends on source). |
| **neutral_site** | Whether the game was played at a neutral site (integer, typically 0/1). |
| **opponent_team_id** | Team ID of the opponent. |

---

## Outcome

| Column | Description |
|--------|--------------|
| **win** | Whether this team won the game (Boolean or 0/1). |

---

## Box score (this game, this team)

Raw stats for **this team in this game** (from `team_box_score` plus game/opponent joins).

| Column | Description |
|--------|--------------|
| **pts** | Points scored. |
| **fgm** | Field goals made. |
| **fga** | Field goals attempted. |
| **fg_pct** | Field goal percentage (fgm / fga). |
| **fg3m** | 3-point field goals made. |
| **fg3a** | 3-point field goals attempted. |
| **fg3_pct** | 3-point field goal percentage. |
| **ftm** | Free throws made. |
| **fta** | Free throws attempted. |
| **ft_pct** | Free throw percentage. |
| **oreb** | Offensive rebounds. |
| **dreb** | Defensive rebounds. |
| **reb** | Total rebounds. |
| **ast** | Assists. |
| **tov** | Turnovers. |
| **stl** | Steals. |
| **blk** | Blocks (by this team). |
| **blka** | Blocks against (this team’s shots that were blocked). |
| **pf** | Personal fouls committed. |
| **pfd** | Personal fouls drawn. |
---

## Advanced (this game, this team)

From the advanced box score CSV backfill (when available).

| Column | Description |
|--------|--------------|
| **pace** | Possessions per 48 minutes (for this team/game in the advanced source). |
| **poss** | Possessions (for this team/game in the advanced source). |

---

## Season-to-date and prior-game stats (per team per season)

All of these reset at the start of each **(team_name, season_year)** and are in game-date order.

| Column | Description |
|--------|--------------|
| **game_number** | Ordinal game number for this team in this season (1, 2, 3, …). |
| **days_rest** | Number of days since this team’s previous game (0 for first game of season). |
| **is_back_to_back** | 1 if the team played the previous calendar day (days_rest == 1), else 0. |
| **total_wins** | Cumulative wins for this team in this season **through this game** (including this game). |
| **total_losses** | Cumulative losses = game_number − total_wins. |
| **win_percentage** | total_wins / game_number (through and including this game). |
| **wins_last_5** | Number of wins in the **5 games before** this one (current game excluded); 0–5. |
| **wins_last_10** | Number of wins in the **10 games before** this one (current game excluded); 0–10. |
| **win_percentage_last_5** | wins_last_5 / 5 (denominator always 5). |
| **win_percentage_last_10** | wins_last_10 / 10 (denominator always 10). |

---

## Differentials (this game)

For each row: **this team’s value minus the opponent’s value** for the same game (so each of the two rows per game gets the correct sign).

| Column | Description |
|--------|--------------|
| **diff_pts** | pts − opponent_pts (for this team). |
| **diff_ast** | ast − opponent’s ast. |
| **diff_tov** | tov − opponent’s tov. |
| **diff_blk** | blk − opponent’s blk. |
| **diff_blka** | blka − opponent’s blka. |
| **diff_fgm** | fgm − opponent’s fgm. |
| **diff_fga** | fga − opponent’s fga. |
| **diff_ftm** | ftm − opponent’s ftm. |
| **diff_fta** | fta − opponent’s fta. |
| **diff_pf** | pf − opponent’s pf. |
| **diff_pfd** | pfd − opponent’s pfd. |
| **diff_stl** | stl − opponent’s stl. |
| **diff_oreb** | oreb − opponent’s oreb. |
| **diff_dreb** | dreb − opponent’s dreb. |
| **diff_fg3m** | fg3m − opponent’s fg3m. |
| **diff_fg3a** | fg3a − opponent’s fg3a. |
| **diff_days_rest** | days_rest − opponent’s days_rest. |
| **diff_win_percentage** | win_percentage − opponent’s win_percentage (season-to-date through this game). |
| **diff_wins_last_5** | wins_last_5 − opponent’s wins_last_5. |
| **diff_wins_last_10** | wins_last_10 − opponent’s wins_last_10. |
| **diff_win_percentage_last_5** | win_percentage_last_5 − opponent’s. |
| **diff_win_percentage_last_10** | win_percentage_last_10 − opponent’s. |

---

## Rolling means (prior 5 games)

Mean over the **5 games immediately before** the current game (current game excluded). Computed per (team_name, season_year) in date order. Column naming: **`<stat>_rolling_mean_prev_5`**.

**Raw box and advanced stats**

- pts_rolling_mean_prev_5, ast_rolling_mean_prev_5, tov_rolling_mean_prev_5, blk_rolling_mean_prev_5, blka_rolling_mean_prev_5  
- fgm_rolling_mean_prev_5, fga_rolling_mean_prev_5, ftm_rolling_mean_prev_5, fta_rolling_mean_prev_5  
- pf_rolling_mean_prev_5, pfd_rolling_mean_prev_5, stl_rolling_mean_prev_5  
- reb_rolling_mean_prev_5, oreb_rolling_mean_prev_5, dreb_rolling_mean_prev_5  
- fg3m_rolling_mean_prev_5, fg3a_rolling_mean_prev_5  
- pace_rolling_mean_prev_5  

**Differentials (prior 5 games)**

- diff_pts_rolling_mean_prev_5, diff_ast_rolling_mean_prev_5, diff_tov_rolling_mean_prev_5, diff_blk_rolling_mean_prev_5, diff_blka_rolling_mean_prev_5  
- diff_fgm_rolling_mean_prev_5, diff_fga_rolling_mean_prev_5, diff_ftm_rolling_mean_prev_5, diff_fta_rolling_mean_prev_5  
- diff_pf_rolling_mean_prev_5, diff_pfd_rolling_mean_prev_5, diff_stl_rolling_mean_prev_5  
- diff_oreb_rolling_mean_prev_5, diff_dreb_rolling_mean_prev_5, diff_fg3m_rolling_mean_prev_5, diff_fg3a_rolling_mean_prev_5  
- diff_days_rest_rolling_mean_prev_5  
- diff_win_percentage_rolling_mean_prev_5, diff_wins_last_5_rolling_mean_prev_5, diff_wins_last_10_rolling_mean_prev_5  
- diff_win_percentage_last_5_rolling_mean_prev_5, diff_win_percentage_last_10_rolling_mean_prev_5  

*(Each is the mean of that stat over the team’s previous 5 games; for diff_* stats it is the mean of the per-game differential over the previous 5 games.)*

---

## Expanding averages (season-to-date)

**Expanding mean** from the first game of the season **through the current game** (including the current game). Computed per (team_name, season_year) in date order. Column naming: **`<stat>_average`**.

**Raw box and advanced stats**

- pts_average, ast_average, tov_average, blk_average, blka_average  
- fgm_average, fga_average, ftm_average, fta_average  
- pf_average, pfd_average, stl_average  
- reb_average, oreb_average, dreb_average  
- fg3m_average, fg3a_average  
- pace_average  

**Differentials (season-to-date)**

- diff_pts_average, diff_ast_average, diff_tov_average, diff_blk_average, diff_blka_average  
- diff_fgm_average, diff_fga_average, diff_ftm_average, diff_fta_average  
- diff_pf_average, diff_pfd_average, diff_stl_average  
- diff_oreb_average, diff_dreb_average, diff_fg3m_average, diff_fg3a_average  
- diff_days_rest_average  
- diff_win_percentage_average, diff_wins_last_5_average, diff_wins_last_10_average  
- diff_win_percentage_last_5_average, diff_win_percentage_last_10_average  

*(Each is the mean of that stat over all of the team’s games so far this season; for diff_* stats it is the mean of the per-game differential over those games.)*

