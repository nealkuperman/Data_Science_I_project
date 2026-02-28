#%%
import sys
import multiprocessing
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import seaborn as sns
import xgboost as xgb
import shap
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, ConfusionMatrixDisplay
from sklearn.model_selection import GridSearchCV
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from source.db import get_engine
from scripts.get_data_from_db import *
from scripts.preprocessing import *

_data_dir = _project_root / "data"
_cleaned_data_dir = _project_root / "cleaned_data"
default_engine = get_engine()

box_score_df = pd.read_csv(_cleaned_data_dir / "cleaned_data_2_21_26.csv")
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
                                'diff_fg3m', 'diff_fg3a', "diff_reb", "wins_last_10_average", "wins_last_5_average",
                                "win_percentage_average", "win_percentage_last_10_average", 
                                "wins_last_10_rolling_mean_prev_10", "win_percentage_rolling_mean_prev_10",
                                "win_percentage_last_10_rolling_mean_prev_10", "diff_wins_last_10", "wins_last_10"] 

unneeded_diff_cols = ['diff_days_rest_average', 'diff_days_rest_rolling_mean_prev_5', 'diff_win_percentage_average',
                        'diff_win_percentage_last_10_average', 'diff_win_percentage_last_10_rolling_mean_prev_5',
                        'diff_win_percentage_last_5_average', 'diff_win_percentage_last_5_rolling_mean_prev_5',
                        'diff_win_percentage_rolling_mean_prev_5', 'diff_wins_last_10_average',
                        'diff_wins_last_10_rolling_mean_prev_5', 'diff_wins_last_5_average',
                        'diff_wins_last_5_rolling_mean_prev_5', "diff_win_percentage_rolling_mean_prev_10"]

col_prefixes = ['diff_days_rest_rolling_mean_prev_', 'diff_win_percentage_last_10_rolling_mean_prev_', 'diff_win_percentage_last_5_rolling_mean_prev_'
'diff_win_percentage_rolling_mean_prev_', 'diff_wins_last_10_rolling_mean_prev_', 'diff_wins_last_5_rolling_mean_prev_']

cols_to_ignore = []
for prefix in col_prefixes:
    cols_to_ignore.extend([col for col in box_score_df.columns if col.startswith(prefix)])

unneeded_cols = unneeded_identifying_cols + unneeded_in_game_stats_cols + unneeded_team_summary_cols + unneeded_diff_cols + cols_to_ignore

x_cols = [col for col in box_score_df.columns if col not in unneeded_cols]
y_cols = ["win", "diff_pts"]
y_col = ["win"]
modeling_df = box_score_df[x_cols + y_cols]

X = box_score_df[x_cols]
y = box_score_df["win"].astype(int)




#%%
# box_score_df = get_processed_box_score_df()
# box_score_df = pd.read_csv(_cleaned_data_dir / "cleaned_data_2_21_26.csv")
# X_log_reg_numeric_cols = ["diff_win_percentage", "diff_wins_last_10", "dreb_average", "diff_blk_average", "diff_days_rest",  "stl_average"]
X_log_reg_numeric_cols = [
    'pace_average',
    'blka_average',
    'pfd_average',
    'diff_fg3a_average',
    'dreb_average',
    'diff_ftm_average',
    'diff_fgm_average',
    'diff_pace_average',
    'diff_days_rest',
    'is_home',
    'diff_pts_average',
    'win_percentage_last_10',
    'diff_win_percentage_last_10',
    'win_percentage',
    'diff_win_percentage'
    ]
X_log_reg_categorical_cols = []

y_log_reg_col = ["win"]


scaler = StandardScaler()

scaled = pd.DataFrame(
    scaler.fit_transform(X[X_log_reg_numeric_cols]),
    columns=X_log_reg_numeric_cols,
    index=X.index,
)
X_log_reg = pd.concat([scaled, X[X_log_reg_categorical_cols].astype("int")], axis=1)


X_train, X_test, y_train, y_test = train_test_split(X_log_reg, y, test_size=0.3, random_state=42, stratify=y)

model = LogisticRegression()


clf = GridSearchCV(
    model,
    {
        "C": range(1, 100, 1)
    },
    verbose=1,
    n_jobs=2,
    cv=10,
)

clf.fit(X_train, y_train)
print(clf.best_score_)
print(clf.best_params_)

model = clf.best_estimator_

model.fit(X_train, y_train)
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred))

# Linear part: z = intercept + sum(coef_i * x_i)
feats = X_train.columns.tolist()
coefs = model.coef_[0]
intercept = model.intercept_[0]

print("z = {:.4f}".format(intercept), end="")
for name, c in zip(feats, coefs):
    sign = "+" if c >= 0 else ""
    print(" {} {:.4f}*{}".format(sign, c, name), end="")
print()
print("P(win) = 1 / (1 + exp(-z))")

# Confusion matrix (sklearn convention: rows = Truth, columns = Predicted)
cm = confusion_matrix(y_test, y_pred)
labels = sorted(pd.unique(y_test))
confusion_df = pd.DataFrame(cm, index=labels, columns=labels)
confusion_df.index.name = "Truth"
confusion_df.columns.name = "Predicted"
print(confusion_df)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
disp.plot(cmap=plt.cm.Blues)
plt.title("Confusion matrix (logistic regression)")
plt.show()
# %%
