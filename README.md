# NBA Game Outcome Prediction

A data science project for predicting NBA game outcomes (win/loss) using team box scores, rolling and expanding averages, and differential features. The pipeline covers data ingestion, preprocessing, and multiple classification models (logistic regression, PCA/PLS + logistic, and XGBoost).

---

## Overview

- **Data:** NBA team game logs and box scores (fetched via `nba_api` or loaded from PostgreSQL).
- **Target:** Binary win/loss per game row (one row per team per game).
- **Features:** Season-to-date and rolling stats (e.g. win%, pts, ast, pace), game context (e.g. `is_home`, `days_rest`), and team-vs-opponent differentials.
- **Models:** Logistic regression (plain and with PCA/PLS dimensionality reduction), XGBoost (full and reduced feature sets), with optional comparison of performance on “upsets” (games where the team with lower win% won).

---

## Setup

### Requirements

- **Python 3.12+** (see `pyproject.toml`; the project uses `uv` or pip).
- **PostgreSQL** (e.g. via Docker) for loading raw data—see [DATABASE_SETUP.md](DATABASE_SETUP.md).
- Key dependencies: `pandas`, `numpy`, `scikit-learn`, `xgboost`, `matplotlib`, `seaborn`, `joblib`, `sqlalchemy`, `psycopg2-binary`, `python-dotenv`, `nba-api`.

### Install

From the project root:

```bash
uv sync
# or
pip install -e .
```

### Database (optional)

If you use the DB for raw data:

1. Copy `.env.example` to `.env` and set `DATABASE_URL` (and optionally `DATABASE_TEST_URL`).
2. Start Postgres: `docker compose up -d`.
3. Load data: `python -m source.load_data` (see [docs/PIPELINE.md](docs/PIPELINE.md)).

---

## Project Structure

```
├── source/                 # DB and loaders
│   ├── db.py               # get_engine(), reads .env
│   ├── load_data.py       # Orchestrates loading into Postgres
│   ├── load_team_data.py
│   ├── load_game_data.py
│   ├── load_team_box_score.py
│   └── ...
├── scripts/
│   ├── pull_NBA_data.py         # Fetch from nba_api → CSVs
│   ├── get_data_from_db.py      # DB helpers / summary
│   ├── preprocessing.py        # Rolling/expanding stats, diffs, pipeline()
│   ├── run_models               # Main entry: train/eval all models, plots, comparisons
│   ├── logistic_reg_models.py  # LogisticRegressor, PCALogisticRegressor, PLSLogisticRegressor
│   ├── gradient_boosted_tree_models.py  # XGBoost training, CV, feature importance
│   └── ...
├── schema/                 # SQL table definitions, reset/check scripts
├── data/                   # Raw CSVs from pull (if used)
├── cleaned_data/           # Processed CSV used for modeling (e.g. cleaned_data_2_21_26.csv)
├── figures/                # Saved plots (confusion matrices, ROC, model comparison, etc.)
├── models/                 # Saved models (joblib: PLS/PCA logistic, XGBoost)
├── docs/
│   ├── PIPELINE.md         # Pull → Load pipeline
│   └── Resources.md        # References (permutation importance, ELO, SHAP, etc.)
├── tests/
├── pyproject.toml
├── docker-compose.yml
└── DATABASE_SETUP.md
```

---

## Data Pipeline

1. **Pull (optional):** `scripts/pull_NBA_data.py` fetches game logs/box scores from the NBA API and writes CSVs to `data/`.
2. **Load (optional):** `source/load_*` scripts (or `python -m source.load_data`) load those CSVs into PostgreSQL.
3. **Preprocessing:** `scripts/preprocessing.py` defines a `pipeline()` that, given a box-score DataFrame:
   - Adds per-team-per-season game order, days rest, back-to-back, cumulative wins, win%.
   - Adds rolling sums/averages (e.g. last 10 games) and expanding averages.
   - Computes team-vs-opponent differentials for selected stats (diffs are per game, both teams).
   - Drops the first game of each team-season (no prior stats).  
   The result can be written to `cleaned_data/` for modeling.
4. **Modeling input:** `run_models` (and the model scripts) read from `cleaned_data/cleaned_data_2_21_26.csv` and use a defined set of feature columns (excluding identifiers, in-game stats that leak the outcome, and some redundant diff columns).

See [docs/PIPELINE.md](docs/PIPELINE.md) for pull/load details and [cleaned_data/GAME_SUMMARY_COLUMNS.md](cleaned_data/GAME_SUMMARY_COLUMNS.md) if present for column notes.

---

## Models

- **Logistic Regression (plain):** `LogisticRegressor` in `logistic_reg_models.py` — `StandardScaler` + `LogisticRegression` with GridSearchCV over `C` (e.g. on a manually chosen subset of features).
- **PCA + Logistic:** `PCALogisticRegressor` — scaler → PCA → logistic; GridSearchCV over `pca__n_components` and `logistic__C`; supports ROC, confusion matrix, and CV-vs-components plots.
- **PLS + Logistic:** `PLSLogisticRegressor` — scaler → custom `PLSTransformer` (wraps `PLSRegression`) → logistic; same tuning and plotting ideas.
- **XGBoost:** In `gradient_boosted_tree_models.py` — full-feature and reduced-feature (e.g. top-k by permutation importance) classifiers; GridSearchCV over depth, n_estimators, gamma, learning_rate, alpha; feature importance and permutation importance plots.

All classifiers predict win (1) vs loss (0) per row. Train/test split is 70/30, stratified on the target.

---

## Running the Models

From the project root, with the virtualenv activated:

```bash
python scripts/run_models
```

This script:

- Loads the cleaned CSV, builds train/test splits and feature sets (`x_cols`, `X_log_reg_numeric_cols`, etc.).
- Trains (or loads from `models/`) logistic, PCA+logistic, PLS+logistic, and XGBoost models.
- Prints accuracies and (where applicable) best CV parameters.
- Saves confusion matrices, ROC curves, and comparison plots (e.g. model accuracy vs winner–loser win% threshold) under `figures/`.
- Can compute misclassification sets and Jaccard similarity across models, and upset-focused metrics (e.g. `count_higher_wp_losses` / win-gap analysis).

To train XGBoost with a full grid search from scratch, use `scripts/gradient_boosted_tree_models.py` (e.g. set `RERUN_GRID_SEARCH = True` or run its `__main__` block).

---

## Outputs

- **figures/** — Confusion matrices (train/test), ROC curves per model, ROC comparison, CV accuracy vs win% difference, XGBoost feature/permutation importance, etc.
- **models/** — Joblib-saved estimators (e.g. `pls_logistic_regressor_60_component.joblib`, `pca_logistic_regressor_60_component.joblib`, `xgb_grid_search.joblib`). Load with `joblib.load()`; ensure the class definitions from `logistic_reg_models` are imported when loading PLS/PCA models.

---

## Tests

From the project root:

```bash
pytest tests/
```

Covers load scripts and DB-related behavior (see `tests/conftest.py` for test DB usage).

---

## References

- [docs/Resources.md](docs/Resources.md) — Links to permutation importance, ELO, SHAP, adjusted plus-minus, and NBA prediction articles/repos.
- [docs/PIPELINE.md](docs/PIPELINE.md) — Pull → Load pipeline and scheduler options.
- [DATABASE_SETUP.md](DATABASE_SETUP.md) — Docker Postgres setup and connection strings.

---

## License

Add your license here.
