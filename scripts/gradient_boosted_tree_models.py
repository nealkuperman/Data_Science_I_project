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
from sklearn.metrics import accuracy_score, confusion_matrix, ConfusionMatrixDisplay
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
_models_dir = _project_root / "models"
_plots_dir = _project_root / "figures"
default_engine = get_engine()


# box_score_df = get_processed_box_score_df()
box_score_df = pd.read_csv(_cleaned_data_dir / "cleaned_data_2_21_26.csv")

#%%

BEST_PARAMS_DEFAULT = {'alpha': 0.2,
                       'gamma': 0.1,
                       'learning_rate': 0.05,
                       'max_depth': 7,
                       'n_estimators': 250
                       }

DEFAULT_PARAM_GRID = {
        "max_depth": [5, 6, 7, 8],
        "n_estimators": [100, 150, 175, 200, 250],
        "gamma": [0.075, 0.1, 0.2, 0.5],
        "learning_rate": [0.05, 0.1, 0.125, 0.15, 0.2],
        "alpha": [0.0, 0.1, 0.2]  # L1 regularization in native xgb
    }

DEFAULT_PARAM_GRID = {
        "max_depth": [5, 6, 7],
        "n_estimators": [100, 150, 175, 200, 250],
        "gamma": [0.075, 0.1, 0.2],
        "learning_rate": [0.05, 0.1, 0.125, 0.15, 0.2],
        "alpha": [0.0, 0.1, 0.2]  # L1 regularization in native xgb
    }


def run_CV_xgboost(xgb_model, X_train, y_train, param_grid = None, cv = 5, save_model= False):
    if param_grid is None:
        param_grid = DEFAULT_PARAM_GRID
   
    clf = GridSearchCV(
        xgb_model,
        param_grid,
        verbose=1,
        # n_jobs=2,
        n_jobs=1,
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
if __name__ == "__main__":
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



    RERUN_GRID_SEARCH = False
    SAVE_MODEL = False

    x_cols = [col for col in box_score_df.columns if col not in unneeded_cols]
    y_cols = ["win", "diff_pts"]
    y_col = ["win"]
    modeling_df = box_score_df[x_cols + y_cols]

    X = box_score_df[x_cols]
    y = box_score_df["win"].astype(int)


    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)


    # ================================================================
    # Train the model
    # ================================================================
    xgb_model = xgb.XGBClassifier(
        # n_jobs=multiprocessing.cpu_count() // 2, tree_method="hist"
        n_jobs=1, tree_method="hist"
    )

    if RERUN_GRID_SEARCH:
        clf = run_CV_xgboost(xgb_model, X_train, y_train, param_grid=DEFAULT_PARAM_GRID, cv=5, save_model=SAVE_MODEL)
        model = clf.best_estimator_
    else:
        clf = joblib.load(_models_dir / "xgb_full_grid_clf_2026-03-03_16-11-54.joblib")
        model = train_xgboost(xgb_model, X_train, y_train, params=BEST_PARAMS_DEFAULT, cv=5, save_model=False)

    # ================================================================
    # Evaluate the model
    # ================================================================
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {accuracy * 100:.2f}%")

    cm = confusion_matrix(y_test, y_pred)
    labels = sorted(pd.unique(y_test)) 
    confusion_df = pd.DataFrame(cm, index=labels, columns=labels)
    confusion_df.index.name = "Truth"
    confusion_df.columns.name = "Predicted"
    print(confusion_df)

    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
    disp.plot(cmap=plt.cm.Blues)
    plt.title("Confusion matrix - Gradient Boosted Tree \nFull Feature Model, Test Set")
    plt.savefig(_plots_dir / "xgb_full_feature_model_confusion_matrix_test.png")
    plt.show()

    # ================================================================
    # Feature importance on test set
    # ================================================================
    IMPORTANCE_THRESHOLD = 1e-5
    top_n_features = 30

    best = model
    feature_names = X_train.columns
    importances = best.feature_importances_
    importance_df = pd.DataFrame({"feature": feature_names, "importance": importances})
    importance_filtered = importance_df[importance_df["importance"] >= IMPORTANCE_THRESHOLD].sort_values(
        by="importance", ascending=True
    ).tail(top_n_features)
    plt.figure(figsize=(8, max(6, len(importance_filtered) * 0.35)))
    plt.barh(importance_filtered["feature"], importance_filtered["importance"])
    plt.xlabel("XGBoost feature importance (Train Set)")
    plt.title(f"XGBoost feature importance (Train Set)\ntop {top_n_features} features")
    plt.tight_layout()
    plt.savefig(_plots_dir / "xgb_full_feature_model_feature_importance_train.png")
    plt.show()

    important_features = importance_filtered["feature"].tolist()
    corr_important_features = X[important_features].corr()

    n_features = len(important_features)
    plt.figure(figsize=(max(8, n_features * 0.5), max(6, n_features * 0.5)))
    sns.heatmap(corr_important_features, annot=True, fmt=".2f", cmap="RdBu_r", center=0, square=True)
    plt.tight_layout()
    plt.show()

    # ================================================================
    # Permutation importance on test set
    # ================================================================
    PERMUTATION_IMPORTANCE_THRESHOLD = 1e-3
    perm = permutation_importance(best, X_test, y_test, n_repeats=20, random_state=42, n_jobs=1)
    sorted_idx_perm = perm.importances_mean.argsort()
    perm_importance_df = pd.DataFrame({
        "feature": feature_names[sorted_idx_perm],
        "permutation_importance_mean": perm.importances_mean[sorted_idx_perm],
    })
    perm_importance_filtered = perm_importance_df[
        perm_importance_df["permutation_importance_mean"].abs() >= 
        PERMUTATION_IMPORTANCE_THRESHOLD
    ].sort_values(by="permutation_importance_mean", ascending=True).tail(top_n_features)

    plt.figure(figsize=(8, max(6, len(perm_importance_filtered) * 0.35)))
    plt.barh(perm_importance_filtered["feature"], perm_importance_filtered["permutation_importance_mean"])
    plt.xlabel("Permutation importance (test set)")
    plt.title(f"Permutation importance of features (Test Set)\ntop {top_n_features} features")
    plt.tight_layout()
    plt.savefig(_plots_dir / "xgb_full_feature_model_permutation_importance_test.png")
    plt.show()

    # ================================================================
    # Rerun with 15 most important features from permutation importance
    # ================================================================
    xgb_model_top = xgb.XGBClassifier(
        # n_jobs=multiprocessing.cpu_count() // 2, tree_method="hist"
        n_jobs=1, tree_method="hist"

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
    labels = sorted(pd.unique(y_test))  
    confusion_df = pd.DataFrame(cm, index=labels, columns=labels)
    confusion_df.index.name = "Truth"
    confusion_df.columns.name = "Predicted"
    print(confusion_df)

    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
    disp.plot(cmap=plt.cm.Blues)
    plt.title("Confusion matrix - Gradient Boosted Tree \nReduced Feature Model, Test Set")
    plt.savefig(_plots_dir / "xgb_reduced_feature_model_confusion_matrix_test.png")
    plt.show()

    # ================================================================
    # Plot CV accuracy vs max_depth, one plot per n_estimators
    # ================================================================
    cv_res = clf.cv_results_
    results_df = pd.DataFrame({
        "max_depth": np.asarray(cv_res["param_max_depth"], dtype=int),
        "n_estimators": np.asarray(cv_res["param_n_estimators"], dtype=int),
        "mean_test_score": cv_res["mean_test_score"],
        "std_test_score": cv_res["std_test_score"],
    })

    n_vals = sorted(results_df["n_estimators"].unique())
    n_plots = len(n_vals)

    fig, axes = plt.subplots(
        nrows=1,
        ncols=n_plots,
        figsize=(4 * n_plots, 4),
        sharey=True,
    )

    # axes is 1D array if n_plots > 1, otherwise a single Axes
    if n_plots == 1:
        axes = [axes]

    for ax, n in zip(axes, n_vals):
        sub = results_df[results_df["n_estimators"] == n].sort_values("max_depth")
        ax.errorbar(
            sub["max_depth"],
            sub["mean_test_score"],
            yerr=sub["std_test_score"],
            marker="o",
            linestyle="-",
        )
        ax.set_title(f"n_estimators = {n}")
        ax.set_xlabel("max_depth")
        ax.grid(True, alpha=0.3)

    axes[0].set_ylabel("CV accuracy")
    fig.suptitle("XGBoost CV: accuracy vs max_depth by n_estimators", y=1.02)
    plt.tight_layout()
    plt.show()


    # ================================================================
    # Plot distbrution of CV accuracy
    # ================================================================
    plt.figure(figsize=(6, 4))
    sns.histplot(data=results_df, x="mean_test_score", bins=20, kde=True)
    plt.xlabel("CV mean_test_score")
    plt.ylabel("Count")
    plt.title("Distribution of CV mean_test_score across XGBoost grid")
    plt.tight_layout()
    plt.savefig(_plots_dir / "xgb_cv_accuracy_distribution.png")
    plt.show()
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
    xgb_model_top = xgb.XGBClassifier(
        # n_jobs=multiprocessing.cpu_count() // 2, tree_method="hist"
        n_jobs=1, tree_method="hist"
    )
    X_train_top = X_train[top_features]
    X_test_top = X_test[top_features]
    clf_top = run_CV_xgboost(xgb_model_top, X_train_top, y_train, param_grid=DEFAULT_PARAM_GRID, cv=5, save_model=False)
    model_top = clf_top.best_estimator_
# %%
    perm_top = permutation_importance(model_top, X_test_top, y_test, n_repeats=20, random_state=42, n_jobs=1)
    sorted_idx_perm_top = perm_top.importances_mean.argsort()
    perm_importance_df_top = pd.DataFrame({
        "feature": feature_names[sorted_idx_perm_top],
        "permutation_importance_mean": perm_top.importances_mean[sorted_idx_perm_top],
    })
    perm_importance_filtered_top = perm_importance_df_top[
        perm_importance_df["permutation_importance_mean"].abs() >= 
        PERMUTATION_IMPORTANCE_THRESHOLD
    ].sort_values(by="permutation_importance_mean", ascending=True)
    plt.figure(figsize=(8, max(6, len(perm_importance_filtered_top) * 0.35)))
    plt.barh(perm_importance_filtered_top["feature"], perm_importance_filtered_top["permutation_importance_mean"])
    plt.xlabel("Permutation importance (test set)")
    plt.title("Permutation importance of features")
    plt.tight_layout()
    plt.show()
# %%
