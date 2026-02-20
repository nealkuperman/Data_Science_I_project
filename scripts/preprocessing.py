#%%
import sys
from pathlib import Path
import pandas as pd
from sympy.printing.pretty.pretty_symbology import G
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.preprocessing import StandardScaler

# When run by path (e.g. python project/source/load_team_data.py), project root may not be on path.
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from source.db import get_engine
from scripts.get_data_from_db import *

_data_dir = _project_root / "data"

default_engine = get_engine()

# -----------------------------------------------------------------------------
# REFERENCE: SQL window functions (same logic as pandas rolling/expanding below).
# Use when you want to do this in the DB – faster for large data. Add to query later.
# -----------------------------------------------------------------------------
# WINDOW DEFINITIONS:
#   w         = partition by (team, season), order by game_date
#   w_roll5   = last 5 rows (current + 4 preceding)  → rolling mean
#   w_expand  = all rows from start of partition     → cumulative/expanding mean
#
# FUNCTIONS:
#   AVG(col) OVER w_roll5   → rolling mean over last 5 games (= pandas .rolling(5).mean())
#   AVG(col) OVER w_expand  → cumulative average to current row (= pandas .expanding().mean())
#   ROW_NUMBER() OVER w     → game number 1,2,3... by date (= pandas .rank(method="first"))
#   LAG(game_date) OVER w   → previous row's game_date; (game_date - LAG(...)) = days_rest
#
# Example – repeat AVG(stat) OVER w_roll5 / w_expand for each stat (ast, tov, pts, ...):
#   SELECT *, AVG(ast) OVER w_roll5 AS ast_rolling_mean_5, AVG(ast) OVER w_expand AS ast_average_10,
#          ROW_NUMBER() OVER w AS game_number,
#          (game_date - LAG(game_date) OVER w)::integer AS days_rest
#   FROM base
#   WINDOW w AS (PARTITION BY team_name, season_year ORDER BY game_date),
#          w_roll5 AS (w ROWS BETWEEN 4 PRECEDING AND CURRENT ROW),
#          w_expand AS (w ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW);
# For point_diff: define in CTE (pts - opponent_pts), then AVG(point_diff) OVER w_roll5 etc.


def running_averages(df, window_size):
    return df.rolling(window=window_size).mean()

#%%

identifying_cols = ["team_name", "season_year", "opponent_name", "team_box_id", 'game_id', 'team_id', 'game_date', 'neutral_site', 'opponent_team_id']


def calc_diffs(g, cols):
    g = g.copy()
    diff_cols = [f"diff_{col}" for col in cols]
    indexs = g.index
    # is_home can be bool or 1/0; ensure we have exactly one home and one away row
    team_1 = g.loc[indexs[0]]
    team_2 = g.loc[indexs[1]]
    team_1_diff = (team_1[cols] - team_2[cols]).values
    team_2_diff = (team_2[cols] - team_1[cols]).values

    g[diff_cols] = float("nan")
    g.loc[indexs[0], diff_cols] = team_1_diff
    g.loc[indexs[1], diff_cols] = team_2_diff
    return g

def add_rolling_averages(df, group_cols, stats, window_size, inplace=False):
    if not inplace:
        df = df.copy()
    
    group = df.shift(1).groupby(group_cols)
    roll = group[stats].transform(lambda x: x.rolling(window=window_size).mean()).fillna(0)
    roll.columns = [f"{s}_rolling_mean_prev_{window_size}" for s in stats]
    df[roll.columns] = roll
    return df

def add_expanding_averages(df, group_cols, stats, inplace=False):
    if not inplace:
        df = df.copy()
    
    group = df.groupby(group_cols)
    avg = group[stats].transform(lambda x: x.expanding().mean()).fillna(0)
    avg.columns = [f"{s}_average" for s in stats]
    df[avg.columns] = avg
    return df


if __name__ == "__main__":
    query = """
        WITH base AS (
            SELECT
                tbs.*,
                g.season_year,
                g.game_date,
                g.minutes_played,
                g.neutral_site,
                CASE WHEN tbs.is_home THEN g.away_team_id ELSE g.home_team_id END AS opponent_team_id
            FROM team_box_score tbs
            JOIN game g ON tbs.game_id = g.game_id
        )
        SELECT
            t.team_name,
            opp.team_name  AS opponent_name,
            tbs_opp.pts    AS opponent_pts,
            base.*
        FROM base
        JOIN team t ON base.team_id = t.team_id
        LEFT JOIN team opp ON opp.team_id = base.opponent_team_id
        LEFT JOIN team_box_score tbs_opp ON tbs_opp.game_id = base.game_id AND tbs_opp.team_id = base.opponent_team_id
    """
    box_score_df = pd.read_sql(query, default_engine)


    # Earlier game first, last game last (per team per season) so rolling/rank are in date order
    box_score_df = box_score_df.sort_values(by=["team_name", "season_year", "game_date"]).reset_index(drop=True)

    # Game number and days rest
    group = box_score_df.groupby(["team_name", "season_year"])
    box_score_df["game_number"] = group["game_date"].transform(lambda x: x.rank(method="first"))
    box_score_df["days_rest"] = group["game_date"].transform(lambda x: x.diff().dt.days).fillna(0)
    box_score_df["is_back_to_back"] = (group["game_date"].transform(lambda x: x.diff().dt.days).fillna(0) == 1).astype(int)
    box_score_df["total_wins"] = group["win"].transform(lambda x: x.cumsum()).astype(int)
    box_score_df["total_losses"] = (box_score_df["game_number"] - box_score_df["total_wins"]).astype(int)
    box_score_df["win_percentage"] = box_score_df["total_wins"] / box_score_df["game_number"]

    # Wins in the 5 prior games (excluding current; resets at start of each team-season)
    box_score_df["wins_last_5"] = (
        group["win"].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum()).fillna(0).astype(int))
    box_score_df["wins_last_10"] = (
        group["win"].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum()).fillna(0).astype(int))
    box_score_df["win_percentage_last_5"] = box_score_df["wins_last_5"] / 5
    box_score_df["win_percentage_last_10"] = box_score_df["wins_last_10"] / 10

#%%
    # Transformed Statistics
    # - differentials for 
    #       'pts', "ast", "tov", "blk", "blka", "fgm", "fga"
    #       'ftm', "fta", "pf", "pfd', "stl", "oreb", "dreb",
    #       "fg3m", "fg3a', 'days_rest', "win_percentage", 
    #       "wins_last_5", "wins_last_10", "win_percentage_last_5", 
    #       "win_percentage_last_10"
    # 

    cols_to_diff = ['pts', "ast", "tov", "blk", 
                    "blka", "fgm", "fga", "ftm", 
                    "fta", "pf", "pfd", "stl", 
                    "oreb", "dreb", "fg3m", "fg3a", 
                    'days_rest', "win_percentage", 
                    "wins_last_5", "wins_last_10", 
                    "win_percentage_last_5", "win_percentage_last_10"]
    diff_df = box_score_df.groupby("game_id")[["game_id"] + cols_to_diff].apply(calc_diffs, cols=cols_to_diff).reset_index(level=0, drop=True).reindex(box_score_df.index)

    diff_cols = [col for col in diff_df.columns if col not in box_score_df.columns]
    box_score_df = pd.concat([box_score_df, diff_df[diff_cols]], axis=1)
#%%
    # By season stats
    # - rolling averages past __ games
    # - pace ranking
    #     - shots per 
    #     - possessions per 
    #     - points per 
    #     - etc.
    # - win/loss percentage
    # - points average
    # - point differential compared to team average 
    group = box_score_df.groupby(["team_name", "season_year"])
    group_cols = ["team_name", "season_year"]
    cols_to_avg = ["pts", "ast", "tov", "blk", "blka", 
             "fgm", "fga", "ftm", "fta", 
             "pf", "pfd", "stl", "reb", 
             "oreb", "dreb", "fg3m", "fg3a",
             "pace"] + diff_cols

    box_score_df = add_rolling_averages(box_score_df, group_cols, cols_to_avg, 5)
    box_score_df = add_expanding_averages(box_score_df, group_cols, cols_to_avg)
    
#%%
    display(box_score_df.head())

    



    x_cols = [col for col in box_score_df.columns if col not in identifying_cols]
    y_cols = ["win"]
    X = box_score_df[x_cols]
    y = box_score_df["win"].astype(int)
    corr = X.corr()

    # for idx, val in corr["win"].sort_values().items():
    #     print(idx, round(val, 4))


# diff_win_percentage 0.4628826375576224
# diff_pts_average 0.32958041209781436

# diff_wins_last_10 0.245674329483666
# # diff_wins_last_5 0.2073831163372514
# diff_ast_average 0.1874072795721165
# win_percentage_last_10 0.1549
# diff_fgm_rolling_mean_prev_5 0.1442
# dreb_average 0.1357
# diff_blk_average 0.1355
# diff_stl_average 0.1301
# is_home 0.1018
# diff_days_rest 0.0575
# diff_blka_average -0.1356
# blk_average 0.0458
# stl_average 0.0673


# diff_win_percentage_rolling_mean_prev_5 0.1867856488923239

# , "win_percentage_last_10" , "diff_fgm_rolling_mean_prev_5", "diff_pts_average", , "diff_ast_average", "diff_stl_average", "blk_average",  "diff_blka_average"



    X_log_reg_numeric_cols = ["diff_win_percentage", "diff_wins_last_10", "dreb_average", "diff_blk_average", "diff_days_rest",  "stl_average"]
    X_log_reg_categorical_cols = ["is_home"]

    y_log_reg_col = ["win"]


    scaler = StandardScaler()


    
    scaled = pd.DataFrame(
        scaler.fit_transform(X[X_log_reg_numeric_cols]),
        columns=X_log_reg_numeric_cols,
        index=X.index,
    )
    X_log_reg = pd.concat([scaled, X[X_log_reg_categorical_cols].astype("int")], axis=1)


    X_train, X_test, y_train, y_test = train_test_split(X_log_reg, y, test_size=0.4, random_state=42)

    model = LogisticRegression()
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
# z = -0.2337 + 1.9248*diff_win_percentage  -0.5559*diff_wins_last_10 + 0.0178*dreb_average  -0.0493*diff_blk_average + 0.1163*diff_days_rest + 0.0220*stl_average + 0.4587*is_home
# P(win) = 1 / (1 + exp(-z))


# %%


teams_query = """
    SELECT t. team_id, team_name
    FROM team t
    """
teams = pd.read_sql(teams_query, default_engine)
print(teams.head())

team_box_score_query = """
    SELECT *
    FROM team_box_score tbs
    """
team_box_score = pd.read_sql(team_box_score_query, default_engine)
print(team_box_score.head())

df = pd.merge(teams[["team_id", "team_name"]], team_box_score, on='team_id', how='left')
print(df.head())

"""
Team stat:
    - rolling averages past __ games
    - league rank prior ___ games
    - pace ranking
        - shots per 



"""
# %%

no_home_game_ids = []
g = df.groupby('game_id')
for game, group in g:
    if group["is_home"].sum()==0:
        # no_home_game_ids.append
        # (group["game_id"].iloc[0])
        no_home_game_ids.append(group["game_id"].iloc[0])
print(no_home_game_ids)
# %%


"""
TO_DO:
    * FIX is_home IN TEAM_BOX_SCORE TABLE. CORRECTED IN GAME TABLE BUT DID NOT UPDATE TEAM_BOX_SCORE TABLE.
    * Look into days rest and try to account for break that cause long days rest (e.g. 11 days diff)

# SOURCE: https://www.nba.com/stats/help/glossary
# PACE: The number of possessions per 48 minutes for a team or player.

"""


