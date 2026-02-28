#%%
import sys
from pathlib import Path
import pandas as pd
from sympy.printing.pretty.pretty_symbology import G
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.preprocessing import StandardScaler
import numpy as np

# When run by path (e.g. python project/source/load_team_data.py), project root may not be on path.
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from source.db import get_engine
from scripts.get_data_from_db import *
from scripts.preprocessing import *

_data_dir = _project_root / "data"

default_engine = get_engine()


df = get_processed_box_score_df()
print(df.head())

#%%

unneeded_identifying_cols = ['team_name','opponent_name', 'opponent_pts', 'team_box_id', 
                                'game_id', 'team_id', 'season_year', 'game_date',  'neutral_site', 
                                'opponent_team_id', 'game_number']

unneeded_in_game_stats_cols = ['win', 'pts', 'fgm', 'fga', 'fg_pct', 'fg3m', 'fg3a', 'fg3_pct', 
                                'ftm', 'fta', 'ft_pct', 'oreb', 'dreb', 'reb', 'ast', 'tov', 
                                'stl', 'blk', 'blka', 'pf', 'pfd', 'pace', 'poss', 'minutes_played']

unneeded_team_summary_cols = ['total_wins', 'total_losses', 'diff_pts', 'diff_ast', 'diff_tov',
                                'total_wins', 'total_losses', 'diff_pts', 'diff_ast', 'diff_tov',
                                'diff_blk', 'diff_blka', 'diff_fgm', 'diff_fga', 'diff_ftm',
                                'diff_fta', 'diff_pf', 'diff_pfd', 'diff_stl', 'diff_oreb', 'diff_dreb',
                                'diff_fg3m', 'diff_fg3a'] 

unneeded_diff_cols = ['diff_days_rest_average', 'diff_days_rest_rolling_mean_prev_5', 'diff_win_percentage_average',
                        'diff_win_percentage_last_10_average', 'diff_win_percentage_last_10_rolling_mean_prev_5',
                        'diff_win_percentage_last_5_average', 'diff_win_percentage_last_5_rolling_mean_prev_5',
                        'diff_win_percentage_rolling_mean_prev_5', 'diff_wins_last_10_average',
                        'diff_wins_last_10_rolling_mean_prev_5', 'diff_wins_last_5_average',
                        'diff_wins_last_5_rolling_mean_prev_5']

col_prefixes = ['diff_days_rest_rolling_mean_prev_', 'diff_win_percentage_last_10_rolling_mean_prev_', 'diff_win_percentage_last_5_rolling_mean_prev_'
'diff_win_percentage_rolling_mean_prev_', 'diff_wins_last_10_rolling_mean_prev_', 'diff_wins_last_5_rolling_mean_prev_']

cols_to_ignore = []
for prefix in col_prefixes:
    cols_to_ignore.extend([col for col in box_score_df.columns if col.startswith(prefix)])

unneeded_cols = unneeded_identifying_cols + unneeded_in_game_stats_cols + unneeded_team_summary_cols + unneeded_diff_cols + cols_to_ignore

x_cols = [
'days_rest', 'wins_last_10', 'wins_last_5', 'win_percentage', 'win_percentage_last_10',
'win_percentage_last_5', 'is_home', 'is_back_to_back',

# diff cols:
'diff_win_percentage', 'diff_win_percentage_last_10', 'diff_win_percentage_last_5',
'diff_wins_last_10', 'diff_wins_last_5', 'diff_days_rest',

# team expanding averages:
'ast_average', 'blk_average', 'blka_average', 'dreb_average', 'fg3a_average',
'fg3m_average', 'fga_average', 'fgm_average', 'fta_average', 'ftm_average',
'oreb_average', 'pace_average', 'pf_average', 'pfd_average', 'pts_average',
'reb_average', 'stl_average', 'tov_average',

# team diff expanding averages:
'diff_ast_average', 'diff_blk_average', 'diff_blka_average', 'diff_dreb_average',
'diff_fg3a_average', 'diff_fg3m_average', 'diff_fga_average', 'diff_fgm_average',
'diff_fta_average', 'diff_ftm_average', 'diff_oreb_average', 'diff_pace_average',
'diff_pf_average', 'diff_pfd_average', 'diff_pts_average', 'diff_stl_average',
'diff_tov_average', 

# team rolling averages (past 5 games):
'ast_rolling_mean_prev_5',  'blk_rolling_mean_prev_5', 'blka_rolling_mean_prev_5',
'dreb_rolling_mean_prev_5', 'fg3a_rolling_mean_prev_5', 'fg3m_rolling_mean_prev_5',
'fga_rolling_mean_prev_5', 'fgm_rolling_mean_prev_5', 'fta_rolling_mean_prev_5',
'ftm_rolling_mean_prev_5', 'oreb_rolling_mean_prev_5', 'pace_rolling_mean_prev_5',
'pf_rolling_mean_prev_5', 'pfd_rolling_mean_prev_5', 'pts_rolling_mean_prev_5',
'reb_rolling_mean_prev_5', 'stl_rolling_mean_prev_5', 'tov_rolling_mean_prev_5',

# team diff rolling averages (past 5 games):
'diff_ast_rolling_mean_prev_5', 'diff_blk_rolling_mean_prev_5', 'diff_blka_rolling_mean_prev_5',
'diff_dreb_rolling_mean_prev_5', 'diff_fg3a_rolling_mean_prev_5', 'diff_fg3m_rolling_mean_prev_5',
'diff_fga_rolling_mean_prev_5', 'diff_fgm_rolling_mean_prev_5', 'diff_fta_rolling_mean_prev_5',
'diff_ftm_rolling_mean_prev_5', 'diff_oreb_rolling_mean_prev_5', 'diff_pace_rolling_mean_prev_5',
'diff_pf_rolling_mean_prev_5', 'diff_pfd_rolling_mean_prev_5', 'diff_pts_rolling_mean_prev_5',
'diff_stl_rolling_mean_prev_5', 'diff_tov_rolling_mean_prev_5']





