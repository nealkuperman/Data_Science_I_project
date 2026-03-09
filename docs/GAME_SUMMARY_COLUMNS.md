# Final game summary: column reference

This document describes every column in the **final game summary** DataFrame produced by `preprocessing.py` (after the main pipeline: query → sort → game/days-rest/wins → diffs → rolling/expanding averages). All rolling and expanding stats are computed **per (team_name, season_year)** in game-date order.

**Conventions used below**

- **diff_*** = for this row’s team, **this team’s value minus the opponent’s value** for that same game (one row per team per game, so each row gets its own differential).
- ***_rolling_mean_prev_5** = mean over the **5 games before** the current game (current game excluded); uses a shifted series so it is “prior games only.”
- ***_average** = **expanding mean** from the start of the season through the current game (including the current game).
- **win_percentage_last_5 / last_10** = wins in the last 5/10 prior games ÷ 5 or 10 (denominator is always 5 or 10 even when fewer games have been played).

**Modeling feature set**  
The win/loss models use a **subset** of the columns below. Tables include a **Used for modeling?** column: **Yes** = included in the final modeling DataFrame; **No** = present in the summary but not used for modeling.

---

## Identifiers and game context

| Column | Description | Used for modeling? |
|--------|--------------|---------------------|
| **team_name** | Name of the team this row describes. | No |
| **opponent_name** | Name of the opposing team in this game. | No |
| **opponent_pts** | Points scored by the opponent in this game. | No |
| **team_box_id** | Primary key of the `team_box_score` row (DB). | No |
| **game_id** | Unique game identifier (DB). | No |
| **team_id** | Team identifier (DB). | No |
| **is_home** | Whether this team was the home team (Boolean or 0/1). | **Yes** |
| **season_year** | Season label (e.g. `"2020-21"`). | No |
| **game_date** | Date of the game. | No |
| **minutes_played** | Game length in minutes (from `game` table; exact definition—e.g. regulation only or including OT—depends on source). | No |
| **neutral_site** | Whether the game was played at a neutral site (integer, typically 0/1). | No |
| **opponent_team_id** | Team ID of the opponent. | No |

---

## Outcome

| Column | Description | Used for modeling? |
|--------|--------------|---------------------|
| **win** | Whether this team won the game (Boolean or 0/1). | No (target only) |

---

## Box score (this game, this team)

Raw stats for **this team in this game** (from `team_box_score` plus game/opponent joins).

| Column | Description | Used for modeling? |
|--------|--------------|---------------------|
| **pts** | Points scored. | No |
| **fgm** | Field goals made. | No |
| **fga** | Field goals attempted. | No |
| **fg_pct** | Field goal percentage (fgm / fga). | No |
| **fg3m** | 3-point field goals made. | No |
| **fg3a** | 3-point field goals attempted. | No |
| **fg3_pct** | 3-point field goal percentage. | No |
| **ftm** | Free throws made. | No |
| **fta** | Free throws attempted. | No |
| **ft_pct** | Free throw percentage. | No |
| **oreb** | Offensive rebounds. | No |
| **dreb** | Defensive rebounds. | No |
| **reb** | Total rebounds. | No |
| **ast** | Assists. | No |
| **tov** | Turnovers. | No |
| **stl** | Steals. | No |
| **blk** | Blocks (by this team). | No |
| **blka** | Blocks against (this team’s shots that were blocked). | No |
| **pf** | Personal fouls committed. | No |
| **pfd** | Personal fouls drawn. | No |
---

## Advanced (this game, this team)

From the advanced box score CSV backfill (when available).

| Column | Description | Used for modeling? |
|--------|--------------|---------------------|
| **pace** | Possessions per 48 minutes (for this team/game in the advanced source). | No |
| **poss** | Possessions (for this team/game in the advanced source). | No |

---

## Season-to-date and prior-game stats (per team per season)

All of these reset at the start of each **(team_name, season_year)** and are in game-date order.

| Column | Description | Used for modeling? |
|--------|--------------|---------------------|
| **game_number** | Ordinal game number for this team in this season (1, 2, 3, …). | No |
| **days_rest** | Number of days since this team’s previous game (0 for first game of season). | **Yes** |
| **is_back_to_back** | 1 if the team played the previous calendar day (days_rest == 1), else 0. | **Yes** |
| **total_wins** | Cumulative wins for this team in this season **through this game** (including this game). | No |
| **total_losses** | Cumulative losses = game_number − total_wins. | No |
| **win_percentage** | total_wins / game_number (through and including this game). | **Yes** |
| **wins_last_5** | Number of wins in the **5 games before** this one (current game excluded); 0–5. | No |
| **wins_last_10** | Number of wins in the **10 games before** this one (current game excluded); 0–10. | No |
| **win_percentage_last_5** | wins_last_5 / 5 (denominator always 5). | No |
| **win_percentage_last_10** | wins_last_10 / 10 (denominator always 10). | **Yes** |

---

## Differentials (this game)

For each row: **this team’s value minus the opponent’s value** for the same game (so each of the two rows per game gets the correct sign).

| Column | Description | Used for modeling? |
|--------|--------------|---------------------|
| **diff_pts** | pts − opponent_pts (for this team). | No |
| **diff_ast** | ast − opponent’s ast. | No |
| **diff_tov** | tov − opponent’s tov. | No |
| **diff_blk** | blk − opponent’s blk. | No |
| **diff_blka** | blka − opponent’s blka. | No |
| **diff_fgm** | fgm − opponent’s fgm. | No |
| **diff_fga** | fga − opponent’s fga. | No |
| **diff_ftm** | ftm − opponent’s ftm. | No |
| **diff_fta** | fta − opponent’s fta. | No |
| **diff_pf** | pf − opponent’s pf. | No |
| **diff_pfd** | pfd − opponent’s pfd. | No |
| **diff_stl** | stl − opponent’s stl. | No |
| **diff_oreb** | oreb − opponent’s oreb. | No |
| **diff_dreb** | dreb − opponent’s dreb. | No |
| **diff_fg3m** | fg3m − opponent’s fg3m. | No |
| **diff_fg3a** | fg3a − opponent’s fg3a. | No |
| **diff_days_rest** | days_rest − opponent’s days_rest. | **Yes** |
| **diff_win_percentage** | win_percentage − opponent’s win_percentage (season-to-date through this game). | **Yes** |
| **diff_wins_last_5** | wins_last_5 − opponent’s wins_last_5. | No |
| **diff_wins_last_10** | wins_last_10 − opponent’s wins_last_10. | No |
| **diff_win_percentage_last_5** | win_percentage_last_5 − opponent’s. | No |
| **diff_win_percentage_last_10** | win_percentage_last_10 − opponent’s. | **Yes** |

---

## Rolling means (prior 5 games)

Mean over the **5 games immediately before** the current game (current game excluded). Computed per (team_name, season_year) in date order. Column naming: **`<stat>_rolling_mean_prev_5`**. **Used for modeling?** No — the models use rolling means over the previous 10 games (see "Rolling means (prior 10 games)").

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

## Rolling means (prior 10 games)

Mean over the **10 games immediately before** the current game (current game excluded). Computed per (team_name, season_year) in date order. Column naming: **`<stat>_rolling_mean_prev_10`**. All of these are **used for modeling**.

**Team rolling means (prior 10)**

| Column | Description | Used for modeling? |
|--------|--------------|---------------------|
| **pts_rolling_mean_prev_10** | Avg points scored over previous 10 games. | **Yes** |
| **ast_rolling_mean_prev_10** | Avg assists over previous 10 games. | **Yes** |
| **tov_rolling_mean_prev_10** | Avg turnovers over previous 10 games. | **Yes** |
| **blk_rolling_mean_prev_10** | Avg blocks over previous 10 games. | **Yes** |
| **blka_rolling_mean_prev_10** | Avg shots blocked against over previous 10 games. | **Yes** |
| **fgm_rolling_mean_prev_10** | Avg field goals made over previous 10 games. | **Yes** |
| **fga_rolling_mean_prev_10** | Avg field goals attempted over previous 10 games. | **Yes** |
| **ftm_rolling_mean_prev_10** | Avg free throws made over previous 10 games. | **Yes** |
| **fta_rolling_mean_prev_10** | Avg free throws attempted over previous 10 games. | **Yes** |
| **pf_rolling_mean_prev_10** | Avg personal fouls committed over previous 10 games. | **Yes** |
| **pfd_rolling_mean_prev_10** | Avg fouls drawn over previous 10 games. | **Yes** |
| **stl_rolling_mean_prev_10** | Avg steals over previous 10 games. | **Yes** |
| **oreb_rolling_mean_prev_10** | Avg offensive rebounds over previous 10 games. | **Yes** |
| **dreb_rolling_mean_prev_10** | Avg defensive rebounds over previous 10 games. | **Yes** |
| **reb_rolling_mean_prev_10** | Avg total rebounds over previous 10 games. | **Yes** |
| **fg3m_rolling_mean_prev_10** | Avg 3PT made over previous 10 games. | **Yes** |
| **fg3a_rolling_mean_prev_10** | Avg 3PT attempted over previous 10 games. | **Yes** |
| **pace_rolling_mean_prev_10** | Avg pace over previous 10 games. | **Yes** |

**Differential rolling means (prior 10): team − opponent**

| Column | Description | Used for modeling? |
|--------|--------------|---------------------|
| **diff_pts_rolling_mean_prev_10** | Team pts rolling mean − opponent, over previous 10. | **Yes** |
| **diff_ast_rolling_mean_prev_10** | Team ast − opponent. | **Yes** |
| **diff_tov_rolling_mean_prev_10** | Team tov − opponent. | **Yes** |
| **diff_blk_rolling_mean_prev_10** | Team blk − opponent. | **Yes** |
| **diff_blka_rolling_mean_prev_10** | Team blka − opponent. | **Yes** |
| **diff_fgm_rolling_mean_prev_10** | Team FGM − opponent. | **Yes** |
| **diff_fga_rolling_mean_prev_10** | Team FGA − opponent. | **Yes** |
| **diff_ftm_rolling_mean_prev_10** | Team FTM − opponent. | **Yes** |
| **diff_fta_rolling_mean_prev_10** | Team FTA − opponent. | **Yes** |
| **diff_pf_rolling_mean_prev_10** | Team PF − opponent. | **Yes** |
| **diff_pfd_rolling_mean_prev_10** | Team PFD − opponent. | **Yes** |
| **diff_stl_rolling_mean_prev_10** | Team STL − opponent. | **Yes** |
| **diff_oreb_rolling_mean_prev_10** | Team OREB − opponent. | **Yes** |
| **diff_dreb_rolling_mean_prev_10** | Team DREB − opponent. | **Yes** |
| **diff_reb_rolling_mean_prev_10** | Team REB − opponent. | **Yes** |
| **diff_fg3m_rolling_mean_prev_10** | Team 3PM − opponent. | **Yes** |
| **diff_fg3a_rolling_mean_prev_10** | Team 3PA − opponent. | **Yes** |
| **diff_pace_rolling_mean_prev_10** | Team pace − opponent. | **Yes** |

---

## Expanding averages (season-to-date)

**Expanding mean** from the first game of the season **through the current game** (including the current game). Computed per (team_name, season_year) in date order. Column naming: **`<stat>_average`**.

**Raw box and advanced stats (all used for modeling)**

| Column | Description | Used for modeling? |
|--------|--------------|---------------------|
| **pts_average** | Season-to-date avg points scored entering the game. | **Yes** |
| **ast_average** | Season-to-date avg assists. | **Yes** |
| **tov_average** | Season-to-date avg turnovers. | **Yes** |
| **blk_average** | Season-to-date avg blocks. | **Yes** |
| **blka_average** | Season-to-date avg shots blocked against. | **Yes** |
| **fgm_average** | Season-to-date avg field goals made. | **Yes** |
| **fga_average** | Season-to-date avg field goals attempted. | **Yes** |
| **ftm_average** | Season-to-date avg free throws made. | **Yes** |
| **fta_average** | Season-to-date avg free throws attempted. | **Yes** |
| **pf_average** | Season-to-date avg personal fouls committed. | **Yes** |
| **pfd_average** | Season-to-date avg fouls drawn. | **Yes** |
| **stl_average** | Season-to-date avg steals. | **Yes** |
| **oreb_average** | Season-to-date avg offensive rebounds. | **Yes** |
| **dreb_average** | Season-to-date avg defensive rebounds. | **Yes** |
| **reb_average** | Season-to-date avg total rebounds. | **Yes** |
| **fg3m_average** | Season-to-date avg 3PT made. | **Yes** |
| **fg3a_average** | Season-to-date avg 3PT attempted. | **Yes** |
| **pace_average** | Season-to-date avg pace. | **Yes** |

**Differentials (season-to-date)**

| Column | Description | Used for modeling? |
|--------|--------------|---------------------|
| **diff_pts_average** | Season-to-date avg (team pts − opponent pts). | **Yes** |
| **diff_ast_average** | Team AST average − opponent. | **Yes** |
| **diff_tov_average** | Team TOV average − opponent. | **Yes** |
| **diff_blk_average** | Team BLK average − opponent. | **Yes** |
| **diff_blka_average** | Team BLKA average − opponent. | **Yes** |
| **diff_fgm_average** | Team FGM average − opponent. | **Yes** |
| **diff_fga_average** | Team FGA average − opponent. | **Yes** |
| **diff_ftm_average** | Team FTM average − opponent. | **Yes** |
| **diff_fta_average** | Team FTA average − opponent. | **Yes** |
| **diff_pf_average** | Team PF average − opponent. | **Yes** |
| **diff_pfd_average** | Team PFD average − opponent. | **Yes** |
| **diff_stl_average** | Team STL average − opponent. | **Yes** |
| **diff_oreb_average** | Team OREB average − opponent. | **Yes** |
| **diff_dreb_average** | Team DREB average − opponent. | **Yes** |
| **diff_reb_average** | Team REB average − opponent. | **Yes** |
| **diff_fg3m_average** | Team 3PM average − opponent. | **Yes** |
| **diff_fg3a_average** | Team 3PA average − opponent. | **Yes** |
| **diff_pace_average** | Team pace average − opponent. | **Yes** |
| **diff_days_rest_average** | Team days_rest average − opponent. | No |
| **diff_win_percentage_average** | Team win% average − opponent. | No |
| **diff_wins_last_5_average** | Team wins_last_5 average − opponent. | No |
| **diff_wins_last_10_average** | Team wins_last_10 average − opponent. | No |
| **diff_win_percentage_last_5_average** | Team win% last 5 avg − opponent. | No |
| **diff_win_percentage_last_10_average** | Team win% last 10 avg − opponent. | No |  

*(Each is the mean of that stat over all of the team’s games so far this season; for diff_* stats it is the mean of the per-game differential over those games.)*

