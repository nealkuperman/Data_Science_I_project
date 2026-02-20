#%%
"""
Request team game logs directly from stats.nba.com (same URL nba.com uses).
Run from project root:  python scripts/request_team_gamelogs.py
"""
import requests
import pandas as pd
from nba_api.stats.static import teams
import time
# Base URL from NBA.com stats (team game logs)
BASE_URL = "https://stats.nba.com/stats/teamgamelogs"

# Headers that match what Chrome sends when you load the stats page (from Network tab)
# Use the exact Referer of the page that makes this request (e.g. boxscores-advanced)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.nba.com/stats/team/1610612738/boxscores-advanced",
    "Origin": "https://www.nba.com",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"macOS"',
}

# Query params matching the URL you found (edit as needed)
PARAMS = {
    "DateFrom": "",
    "DateTo": "",
    "GameSegment": "",
    "ISTRound": "",
    "LastNGames": 0,
    "LeagueID": "00",
    "Location": "",
    "MeasureType": "Advanced",   # Advanced box score
    "Month": 0,
    "OpponentTeamID": 0,
    "Outcome": "",
    "PORound": 0,
    "PaceAdjust": "N",
    "PerMode": "Totals",
    "Period": 0,
    "PlusMinus": "N",
    "Rank": "N",
    "Season": "2025-26",
    "SeasonSegment": "",
    "SeasonType": "Regular Season",
    "ShotClockRange": "",
    "TeamID": 0,        # match the page you found; use 0 for all teams
    "VsConference": "",
    "VsDivision": "",
}


def fetch_team_gamelogs(params=None, use_session=True):
    """
    Request team game logs from stats.nba.com. Returns DataFrame.
    If use_session=True, first visits the stats page to get cookies, then requests the API.
    """
    p = {**PARAMS, **(params or {})}
    session = requests.Session()
    session.headers.update(HEADERS)

    if use_session:
        # Visit the page that makes this request so we get any required cookies
        stats_page = "https://www.nba.com/stats/team/1610612738/boxscores-advanced"
        session.get(stats_page, timeout=15)

    resp = session.get(BASE_URL, params=p, timeout=30)
    if resp.status_code != 200:
        raise requests.RequestException(f"Status {resp.status_code}: {resp.text[:200]}")
    data = resp.json()
    # NBA API returns { "resultSets": [ { "name": "...", "headers": [...], "rowSet": [[...], ...] } ] }
    if not data.get("resultSets"):
        return pd.DataFrame()
    rs = data["resultSets"][0]
    return pd.DataFrame(rs["rowSet"], columns=rs["headers"])


if __name__ == "__main__":
    print("Requesting team game logs (Advanced) from stats.nba.com...")
    teams_lst = teams.get_teams()
    all_data = []
    missing_data = []
    for season in range(2020, 2025):
        season_str = f"{season}-{str(season + 1)[-2:]}"
        params = PARAMS.copy()
        params["Season"] = season_str
        for i, team in enumerate(teams_lst):
            time.sleep(0.6)
            print(f"[{i+1}/30] Requesting team game logs for {team['full_name']}...")
            # params = PARAMS.copy()
            params["TeamID"] = team["id"]
            try:
                df = fetch_team_gamelogs(params, use_session=True)
                # print(f"Rows: {len(df)}")
                if len(df) > 0:
                    # print(df.head())
                    print(f"\t fetched games!")
                else:
                    print("No rows with session. Trying without session...")
                    df = fetch_team_gamelogs(params, use_session=False)
                    print(f"Rows: {len(df)}")
                    if len(df) > 0:
                        print(df.head())
                    else:
                        print(f"skipping {team['full_name']} for {season_str}...")
                        missing_data.append([team['full_name'], season_str])
                        # params["Season"] = "2024-25"
                        # df = fetch_team_gamelogs(params, use_session=True)
                        # print(f"Rows: {len(df)}")
                        # if len(df) > 0:
                        #     print(df.head())
                        continue
                all_data.append(df)
            except requests.RequestException as e:
                print(f"Request failed: {e}")
                missing_data.append([team['full_name'], season_str])
                continue
    all_data = pd.concat(all_data, ignore_index=True)
    all_data.to_csv("team_game_logs_advanced_2020_2025.csv", index=False)
# %%
