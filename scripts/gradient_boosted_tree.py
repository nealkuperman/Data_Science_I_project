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


_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from source.db import get_engine
from scripts.get_data_from_db import *
from scripts.preprocessing import *

_data_dir = _project_root / "data"
_cleaned_data_dir = _project_root / "cleaned_data"
default_engine = get_engine()


# box_score_df = get_processed_box_score_df()
box_score_df = pd.read_csv(_cleaned_data_dir / "cleaned_data_2_21_26.csv")

#%%


BEST_PARAMS_DEFAULT = {'gamma': 0.2, 'learning_rate': 0.15, 'max_depth': 5, 'n_estimators': 175}
BEST_PARAMS_DEFAULT = {'gamma': 0.1, 'learning_rate': 0.125, 'max_depth': 7, 'n_estimators': 200}


DEFAULT_PARAM_GRID = {
        "max_depth": [5, 6, 7, 8],
        "n_estimators": [100, 150, 175, 200, 250],
        "gamma": [0.075, 0.1, 0.2, 0.5],
        "learning_rate": [0.05, 0.1, 0.125, 0.15, 0.2],
        # "alpha": [0.0, 0.1, 0.2]  # eta in native xgb
    }

def run_CV_xgboost(xgb_model, X_train, y_train, param_grid = None, cv = 5, save_model= False):
    if param_grid is None:
        param_grid = DEFAULT_PARAM_GRID
    clf = GridSearchCV(
        xgb_model,
        param_grid,
        verbose=1,
        n_jobs=2,
        cv=cv,
    )

    clf.fit(X_train, y_train)
    print(clf.best_score_)
    print(clf.best_params_)
    if save_model:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        joblib.dump(clf.best_estimator_, _project_root / "models" / f"xgb_best_model_{timestamp}.joblib")
    return clf

def train_xgboost(xgb_model, X_train, y_train, params = None, param_grid= None, cv = 5, save_model= False):
    if param_grid:
        clf = run_CV_xgboost(xgb_model, X_train, y_train, param_grid=param_grid, cv=cv, save_model=save_model)
        model = clf.best_estimator_
    else:
        if params is None:
            params = BEST_PARAMS_DEFAULT
        model = xgb_model.set_params(**params)
        model.fit(X_train, y_train)
        print(model.score(X_train, y_train))
        print(model.get_params())
        if save_model:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            joblib.dump(model, _project_root / "models" / f"xgb_model_{timestamp}.joblib")
    return model

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





x_cols = [col for col in box_score_df.columns if col not in unneeded_cols]
y_cols = ["win", "diff_pts"]
y_col = ["win"]
modeling_df = box_score_df[x_cols + y_cols]

X = box_score_df[x_cols]
y = box_score_df["win"].astype(int)


X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)


# Make sure the number of threads is balanced.
xgb_model = xgb.XGBClassifier(
    n_jobs=multiprocessing.cpu_count() // 2, tree_method="hist"
)

# clf = run_CV_xgboost(xgb_model, X_train, y_train, param_grid=DEFAULT_PARAM_GRID, cv=5, save_model=False)
# model = clf.best_estimator_
model = train_xgboost(xgb_model, X_train, y_train, params=BEST_PARAMS_DEFAULT, cv=5, save_model=False)

y_pred = model.predict(X_test)
# Evaluate the model
accuracy = accuracy_score(y_test, y_pred)
print(f"Accuracy: {accuracy * 100:.2f}%")


cm = confusion_matrix(y_test, y_pred)
labels = sorted(pd.unique(y_test))  # e.g. [0, 1] or use ["loss", "win"] if you prefer
confusion_df = pd.DataFrame(cm, index=labels, columns=labels)
confusion_df.index.name = "Truth"
confusion_df.columns.name = "Predicted"
print(confusion_df)
# Optional: plot with ConfusionMatrixDisplay
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
disp.plot(cmap=plt.cm.Blues)
plt.title("Full Feature Model: Confusion matrix")
plt.show()

# Feature importance (XGBoost) and optional permutation importance

best = model
feature_names = X_train.columns
importances = best.feature_importances_
importance_df = pd.DataFrame({"feature": feature_names, "importance": importances})
importance_filtered = importance_df[importance_df["importance"] >= 1e-5].sort_values(
    by="importance", ascending=True
)
plt.figure(figsize=(8, max(6, len(importance_filtered) * 0.35)))
plt.barh(importance_filtered["feature"], importance_filtered["importance"])
plt.xlabel("XGBoost feature importance")
plt.tight_layout()
plt.show()


important_features = importance_filtered["feature"].tolist()
corr_important_features = X[important_features].corr()

n_features = len(important_features)
plt.figure(figsize=(max(8, n_features * 0.5), max(6, n_features * 0.5)))
sns.heatmap(corr_important_features, annot=True, fmt=".2f", cmap="RdBu_r", center=0, square=True)
plt.tight_layout()
plt.show()



# Permutation importance on test set (optional; slower)
perm = permutation_importance(best, X_test, y_test, n_repeats=20, random_state=42, n_jobs=-1)
sorted_idx_perm = perm.importances_mean.argsort()
perm_importance_df = pd.DataFrame({
    "feature": feature_names[sorted_idx_perm],
    "permutation_importance_mean": perm.importances_mean[sorted_idx_perm],
})
perm_importance_filtered = perm_importance_df[
    perm_importance_df["permutation_importance_mean"].abs() >= 1e-3
].sort_values(by="permutation_importance_mean", ascending=True)

plt.figure(figsize=(8, max(6, len(perm_importance_filtered) * 0.35)))
plt.barh(perm_importance_filtered["feature"], perm_importance_filtered["permutation_importance_mean"])
plt.xlabel("Permutation importance (test set)")
plt.title("Permutation importance of features")
plt.tight_layout()
plt.show()



# Rerun with 10 most important features from permutation importance
xgb_model_top = xgb.XGBClassifier(
    n_jobs=multiprocessing.cpu_count() // 2, tree_method="hist"
)

n_features = 15
top_features = perm_importance_filtered.iloc[-n_features:]["feature"].values.tolist()
X_train_top = X_train[top_features]
X_test_top = X_test[top_features]
model_top = train_xgboost(xgb_model_top, X_train_top, y_train, params=BEST_PARAMS_DEFAULT, cv=5, save_model=False)
y_pred_top = model_top.predict(X_test_top)
accuracy_top = accuracy_score(y_test, y_pred_top)
print(f"Accuracy: {accuracy_top * 100:.2f}%")


cm = confusion_matrix(y_test, y_pred_top)
labels = sorted(pd.unique(y_test))  # e.g. [0, 1] or use ["loss", "win"] if you prefer
confusion_df = pd.DataFrame(cm, index=labels, columns=labels)
confusion_df.index.name = "Truth"
confusion_df.columns.name = "Predicted"
print(confusion_df)
# Optional: plot with ConfusionMatrixDisplay
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
disp.plot(cmap=plt.cm.Blues)
plt.title("Reduced Feature Model: Confusion matrix")
plt.show()



# lambda controls L2 regularization on leaf weights, encouraging small weights, while gamma controls the minimum loss reduction needed to make a split, penalizing the number of leaves

# %%


# # Use best params from GridSearchCV above; train native Booster for SHAP (pred_contribs)
# params = {
#     "objective": "binary:logistic",
#     "max_depth": clf.best_params_["max_depth"],
#     "gamma": clf.best_params_["gamma"],
#     "eta": clf.best_params_.get("learning_rate", 0.3),  # learning_rate in sklearn = eta in xgb
#     "tree_method": "hist",
#     "nthread": multiprocessing.cpu_count() // 2,
# }
# num_boost_round = clf.best_params_["n_estimators"]

# dtrain = xgb.DMatrix(X_train, label=y_train)
# booster = xgb.train(params, dtrain, num_boost_round=num_boost_round)

# shap_values = booster.predict(dtrain, pred_contribs=True)
# pred = booster.predict(dtrain, output_margin=True)

# explainer = shap.TreeExplainer(booster)
# explanation = explainer(dtrain)

# shap_values = explanation.values
# # make sure the SHAP values add up to marginal predictions
# np.abs(shap_values.sum(axis=1) + explanation.base_values - pred).max()# %%
# shap.plots.beeswarm(explanation)

# %%
