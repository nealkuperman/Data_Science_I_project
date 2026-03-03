#%%
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, ConfusionMatrixDisplay
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cross_decomposition import PLSRegression
from sklearn.base import BaseEstimator, TransformerMixin

import polars as pl
import joblib

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from source.db import get_engine
from scripts.get_data_from_db import *
from scripts.preprocessing import *

_data_dir = _project_root / "data"
_cleaned_data_dir = _project_root / "cleaned_data"
_plots_dir = _project_root / "figures"
_models_dir = _project_root / "models"
default_engine = get_engine()

RANDOM_STATE = 42
#%%

class LogisticRegressor:
    def __init__(self, max_iter=1000):
        self.max_iter = max_iter
        self.cv = 10
        self.scoring = "accuracy"
        self.n_jobs = 1  # avoid loky worker timeout / memory issues
        self.refit = True
        self.clf = None

    def _make_pipeline(self):
        return Pipeline([
            ("scaler", StandardScaler()),
            ("lr", LogisticRegression(max_iter=self.max_iter))
        ])
    
    def fit(self, X, y, param_grid=None):
        if param_grid is None:
            param_grid = {
                "lr__C": np.logspace(-3, 3, 30)}
        self.clf = GridSearchCV(
            self._make_pipeline(),
            param_grid=param_grid,
            cv=self.cv,
            scoring=self.scoring,
            n_jobs=self.n_jobs,
            refit=self.refit
        )
        self.clf.fit(X, y)
        return self
    
    def score(self, X, y):
        return self.clf.score(X, y)
    
    def predict(self, X):
        return self.clf.predict(X)


    def run(self, X_train, y_train, X_test, y_test, param_grid=None):
        self.fit(X_train, y_train, param_grid=param_grid)

        y_pred = self.clf.predict(X_test)

        # Print the best parameters and the test accuracy
        print("CV accuracy (train CV):", self.clf.best_score_)
        print("Best params:", self.clf.best_params_)
        print("Test accuracy:", accuracy_score(y_test, y_pred))

        return self
    
    def plt_confusion_matrix(self, X_test, y_test, save_path=None):
        y_pred = self.predict(X_test)
        cm = confusion_matrix(y_test, y_pred, labels=[0,1])
        disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=[0,1])
        disp.plot(cmap=plt.cm.Blues)
        plt.title("Confusion matrix (logistic regression)")
        if save_path is not None:
            plt.savefig(save_path)
        plt.show()
        return self

    def print_logistic_regression_equation(self, X_train):
        feats = X_train.columns.tolist()
        coefs = self.clf.best_estimator_.named_steps["lr"].coef_[0]
        intercept = self.clf.best_estimator_.named_steps["lr"].intercept_[0]

        print("z = {:.4f}".format(intercept), end="")
        for name, c in zip(feats, coefs):
            sign = "+" if c >= 0 else ""
            print(" {} {:.4f}*{}".format(sign, c, name), end="")
        print()
        print("P(win) = 1 / (1 + exp(-z))")


class PCALogisticRegressor:
    def __init__(self, max_components=20, C_grid=None, cv=10, scoring="accuracy", n_jobs=1, refit=True):
        self.max_components = max_components
        self.C_grid = C_grid if C_grid is not None else np.logspace(-3, 3, 15)
        self.cv = cv
        self.scoring = scoring
        self.n_jobs = n_jobs
        self._cv_search_ = None  # will hold the fitted GridSearchCV
        self.refit = refit

    def _make_pipeline(self):
        return Pipeline([
            ("scaler", StandardScaler()),
            ("pca", PCA()),
            ("logistic", LogisticRegression(max_iter=10000))
        ])
    
    def fit(self, X, y, param_grid=None):
        # PCA requires n_components <= min(n_samples, n_features); cap to avoid fit failures in CV
        data_max_components = min(X.shape[0], X.shape[1])
        effective_max = min(self.max_components, data_max_components)
        n_components_options = list(range(1, effective_max + 1))
        if not n_components_options:
            n_components_options = [data_max_components]

        if param_grid is None:
            param_grid = {
                    "pca__n_components": n_components_options,
                    "logistic__C": self.C_grid,
            }

        pipe = self._make_pipeline()
        self._cv_search_ = GridSearchCV(
            pipe,
            param_grid=param_grid,
            cv=self.cv,
            scoring=self.scoring,
            n_jobs=self.n_jobs,
            refit=self.refit
        )

        self._cv_search_.fit(X, y)
        return self
    
    def score(self, X, y):
        return self._cv_search_.score(X, y)
    
    def predict(self, X):
        return self._cv_search_.predict(X)
    
    def best_params_(self):
        return self._cv_search_.best_params_
    
    def get_best_estimator(self, X_train, y_train, n_components=None):
        if n_components is None:
            n_components = int(self._cv_search_.best_params_["pca__n_components"])
        est = self._cv_search_.best_estimator_
        est.named_steps["pca"].n_components = n_components
        est.fit(X_train, y_train)
        return est
    
    def run(self, X_train, y_train, X_test, y_test, param_grid=None, refit=False):
        if refit or self._cv_search_ is None:
            self.fit(X_train, y_train, param_grid=param_grid)
        print("Best CV accuracy:", self._cv_search_.best_score_)
        print("Best parameters:", self._cv_search_.best_params_)
        print("Test accuracy:", self.score(X_test, y_test))

        self.plot_cv_vs_components()
        self.plt_confusion_matrix(X_test, y_test)
        self.plt_confusion_matrix(X_train, y_train, is_test=False)
        return self
    
    def print_logistic_regression_equation(self, X_train, y_train, n_components=None):
        if n_components is None:
            n_components = int(self._cv_search_.best_params_["pca__n_components"])
        est = self.get_best_estimator(X_train, y_train, n_components)
        lr = est.named_steps["logistic"]
        intercept = lr.intercept_[0]
        coefs = lr.coef_[0]
        comp_names = [f"PC{i+1}" for i in range(len(coefs))]
        print("z = {:.4f}".format(intercept), end="")
        for name, c in zip(comp_names, coefs):
            sign = "+" if c >= 0 else ""
            print(" {} {:.4f}*{}".format(sign, c, name), end="")
        print()
        print("P(win) = 1 / (1 + exp(-z))")
        print()
        return self

    def plt_confusion_matrix(self, X, y, is_test=True, save_path=None):
        y_pred = self.predict(X)
        cm = confusion_matrix(y, y_pred, labels=[0,1])
        disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=[0,1])
        disp.plot(cmap=plt.cm.Blues)
        if is_test:
            title = "Confusion matrix (PCA + Logistic Regression) (test)"
        else:
            title = "Confusion matrix (PCA + Logistic Regression) (train)"
        plt.title(title)
        if save_path is not None:
            plt.savefig(save_path)
        plt.show()

    def plot_cv_vs_components(self, save_path=None):
        pca = self._cv_search_.best_estimator_.named_steps["pca"]
        fig, (ax0, ax1) = plt.subplots(nrows=2, sharex=True, figsize=(6, 6))
        ax0.plot(
            np.arange(1, pca.n_components_ + 1), pca.explained_variance_ratio_, "+", linewidth=2
        )
        ax0.set_ylabel("PCA explained variance ratio")

        ax0.axvline(
            self._cv_search_.best_estimator_.named_steps["pca"].n_components,
            linestyle=":",
            label="n_components chosen",
        )
        ax0.legend(prop=dict(size=12))

        ax0.axvline(
            self._cv_search_.best_estimator_.named_steps["pca"].n_components,
            linestyle=":",
            label="n_components chosen",
        )
        ax0.legend(prop=dict(size=12))

        # For each number of components, find the best classifier results
        components_col = "param_pca__n_components"
        is_max_test_score = pl.col("mean_test_score") == pl.col("mean_test_score").max()
        best_clfs = (
            pl.LazyFrame(self._cv_search_.cv_results_)
            .filter(is_max_test_score.over(components_col))
            .unique(components_col)
            .sort(components_col)
            .collect()
        )
        ax1.errorbar(
            best_clfs[components_col],
            best_clfs["mean_test_score"],
            yerr=best_clfs["std_test_score"],
        )
        ax1.set_ylabel("Classification accuracy (val)")
        ax1.set_xlabel("n_components")

        plt.xlim(-1, pca.n_components_ + 1)

        plt.tight_layout()
        if save_path is not None:
            plt.savefig(save_path)
        plt.show()

# ------------------------------------------------------------
# Custom PLS Logistic Regression Class
# ------------------------------------------------------------
class PLSTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, n_components=2):
        self.n_components = n_components

    def fit(self, X, y):
        self.pls_ = PLSRegression(
            n_components=self.n_components,
            scale=False  # we already scale in pipeline
        )
        self.pls_.fit(X, y)
        return self

    def transform(self, X):
        return self.pls_.transform(X)

class PLSLogisticRegressor:
    def __init__(
        self,
        max_components: int = 20,
        C_grid=None,
        cv: int = 10,
        scoring: str = "accuracy",
        n_jobs: int = 1,  # avoid loky worker timeout / memory issues
    ):
        self.max_components = max_components
        self.C_grid = C_grid if C_grid is not None else np.logspace(-3, 3, 15)
        self.cv = cv
        self.scoring = scoring
        self.n_jobs = n_jobs
        self._cv_search_ = None  # will hold the fitted GridSearchCV

    def _make_pipeline(self):
        return Pipeline([
            ("scaler", StandardScaler()),
            ("pls", PLSTransformer()),
            ("logistic", LogisticRegression(max_iter=10000)),
        ])

    def fit(self, X_train, y_train, param_grid=None):
        y_train = np.ravel(y_train)

        max_components = min(self.max_components, X_train.shape[1])
        
        if param_grid is None:
            param_grid = {
                "pls__n_components": range(1, max_components + 1),
                "logistic__C": self.C_grid,
            }

        pipe = self._make_pipeline()
        self._cv_search_ = GridSearchCV(
            pipe,
            param_grid=param_grid,
            cv=self.cv,
            scoring=self.scoring,
            n_jobs=self.n_jobs,
            refit=True,
        )
        print(f"Fitting PLS + Logistic Regression with param_grid: {param_grid}")
        self._cv_search_.fit(X_train, y_train)
        return self  

    def score(self, X_test, y_test):
        return self._cv_search_.score(X_test, np.ravel(y_test))

    def predict(self, X):
        return self._cv_search_.predict(X)

    def best_params_(self):
        return self._cv_search_.best_params_

    def get_best_estimator(self, X_train, y_train, n_components=None):
        if self._cv_search_ is None:
            raise ValueError("GridSearchCV has not been fit yet")

        # If n_components is not provided, use the best n_components from the grid search
        if n_components is None:
            n_components = int(self._cv_search_.best_params_["pls__n_components"])

        cv = self._cv_search_
        res = cv.cv_results_

        # 1. Find all rows with pls__n_components == n
        comps = np.array(res["param_pls__n_components"], dtype=int)
        mask = comps == n_components
        if not mask.any():
            raise ValueError(f"n_components={n_components} was not tried in the grid search")

        # 2. Among those rows, pick the one with highest mean_test_score
        mean_scores = np.array(res["mean_test_score"])
        idx_candidates = np.where(mask)[0]
        best_idx_for_n = idx_candidates[mean_scores[idx_candidates].argmax()]

        # 3. Build and fit an estimator with those params on the full training data
        params_for_n = res["params"][best_idx_for_n]
        est_n = cv.estimator.set_params(**params_for_n)
        est_n.fit(X_train, y_train)
        return est_n

    def plot_cv_vs_components(self, save_path=None):
        components_col = "param_pls__n_components"
        c = self._cv_search_.cv_results_[components_col]
        max_components_used = int(np.max(np.asarray(c)))
        best_clfs = (
            pl.LazyFrame(self._cv_search_.cv_results_)
            .group_by(components_col)
            .agg(
                pl.col("mean_test_score").max().alias("mean_test_score"),
                pl.col("std_test_score").max().alias("std_test_score"),
            )
            .sort(components_col)
            .collect()
        )

        plt.errorbar(
            best_clfs[components_col],
            best_clfs["mean_test_score"],
            yerr=best_clfs["std_test_score"],
        )
        plt.xlim(-1, max_components_used + 1)
        plt.xticks(range(0, max_components_used + 1, 5))
        plt.xlabel("Number of components")
        plt.ylabel("Test accuracy")
        plt.title("PLS + Logistic Regression")
        plt.tight_layout()
        if save_path is not None:
            plt.savefig(save_path)
        plt.show()

    def run(self, X_train, y_train, X_test, y_test, param_grid=None, refit=True):
        if refit or self._cv_search_ is None:
            self.fit(X_train, y_train, param_grid=param_grid)
        print("Best CV accuracy:", self._cv_search_.best_score_)
        print("Best parameters:", self._cv_search_.best_params_)
        print("Test accuracy:", self.score(X_test, y_test))

        self.plot_cv_vs_components()

    def plt_confusion_matrix(self, X_test, y_test, save_path=None):
        y_pred = self.predict(X_test)
        cm = confusion_matrix(y_test, y_pred, labels=[0,1])
        disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=[0,1])
        disp.plot(cmap=plt.cm.Blues)
        plt.title("Confusion matrix (PLS + Logistic Regression)")
        if save_path is not None:
            plt.savefig(save_path)
        plt.show()

    def print_logistic_regression_equation(self, X_train, y_train, n_components=None):
        if n_components is None:
            n_components = int(self._cv_search_.best_params_["pls__n_components"])
        est = self.get_best_estimator(X_train, y_train, n_components)
        lr = est.named_steps["logistic"]
        intercept = lr.intercept_[0]
        coefs = lr.coef_[0]
        comp_names = [f"PC{i+1}" for i in range(len(coefs))]
        print("z = {:.4f}".format(intercept), end="")
        for name, c in zip(comp_names, coefs):
            sign = "+" if c >= 0 else ""
            print(" {} {:.4f}*{}".format(sign, c, name), end="")
        print()
        print("P(win) = 1 / (1 + exp(-z))")
        print()


if __name__ == "__main__":
    box_score_df = pd.read_csv(_cleaned_data_dir / "cleaned_data_2_21_26.csv")


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


    X = box_score_df[x_cols]
    y = box_score_df["win"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=RANDOM_STATE, stratify=y
    )

    # %%

    # Manually filtered features
    X_mf = box_score_df[X_log_reg_numeric_cols]
    y_mf = box_score_df["win"].astype(int)
    logistic_param_grid={"lr__C": range(1, 100)}
    X_train_mf = X_train[X_log_reg_numeric_cols]
    X_test_mf = X_test[X_log_reg_numeric_cols]
    y_train_mf = y_train
    y_test_mf = y_test


    log_reg_clf = LogisticRegressor()
    log_reg_clf.run(X_train_mf, y_train_mf, X_test_mf, y_test_mf, param_grid=logistic_param_grid)

    log_reg_clf.plt_confusion_matrix(X_test_mf, y_test_mf, save_path=_plots_dir / "log_reg_test_confusion_matrix.png")
    log_reg_clf.plt_confusion_matrix(X_train_mf, y_train_mf, save_path=_plots_dir / "log_reg_train_confusion_matrix.png")


    # DataFrame of coefficients and feature names, sorted by coefficient value
    coef_df = pd.DataFrame({
        "feature": X_train_mf.columns.tolist(),
        "coef": log_reg_clf.clf.best_estimator_.named_steps["lr"].coef_[0],
        'abs_coef': np.abs(log_reg_clf.clf.best_estimator_.named_steps["lr"].coef_[0])
    }).sort_values("abs_coef", ascending=False)
    coef_df


    #%%

    LOAD_MODELS = True
    SAVE_MODELS = False

    if LOAD_MODELS:
        _project_root = Path(__file__).resolve().parent.parent
        pls = joblib.load(_models_dir / "pls_logistic_regressor_60_component.joblib")
    else:


        param_grid = {
            "pls__n_components": range(1, 60 + 1),
            "logistic__C": np.logspace(-3, 3, 15),
        }

        pls = PLSLogisticRegressor(max_components=60)
        pls.run(X_train, y_train, X_test, y_test, param_grid=param_grid, refit=True)
        if SAVE_MODELS:
            _models_dir.mkdir(parents=True, exist_ok=True)
            joblib.dump(pls, _models_dir / "pls_logistic_regressor_60_component.joblib")

    pls.plt_confusion_matrix(X_test, y_test, save_path=_plots_dir / "pls_test_confusion_matrix.png")
    pls.plt_confusion_matrix(X_train, y_train, save_path=_plots_dir / "pls_train_confusion_matrix.png")
    pls.plot_cv_vs_components(save_path=_plots_dir / "pls_cv_vs_components.png")
    pls.print_logistic_regression_equation(X_train, y_train)



    #%%

    if LOAD_MODELS:
        pca = joblib.load(_models_dir / "pca_logistic_regressor_60_component.joblib")
    else:
        param_grid = {
            "pca__n_components": range(1, 60 + 1),
            "logistic__C": np.logspace(-3, 3, 15),
        }
        pca = PCALogisticRegressor(max_components=60)
        pca.run(X_train, y_train, X_test, y_test, param_grid=param_grid, refit=True)
        if SAVE_MODELS:
            _models_dir.mkdir(parents=True, exist_ok=True)
            joblib.dump(pca, _models_dir / "pca_logistic_regressor_60_component.joblib")
    
    pca.print_logistic_regression_equation(X_train, y_train)
    pca.plt_confusion_matrix(X_test, y_test, save_path=_plots_dir / "pca_test_confusion_matrix.png")
    pca.plt_confusion_matrix(X_train, y_train, save_path=_plots_dir / "pca_train_confusion_matrix.png")
    pca.plot_cv_vs_components(save_path=_plots_dir / "pca_cv_vs_components.png")



# %%




