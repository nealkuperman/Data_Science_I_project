#%% Import Libraries
from nba_api.stats.static import teams, players
from nba_api.stats.endpoints import (cumestatsteamgames, 
                                    cumestatsteam, 
                                    gamerotation, 
                                    teamgamelogs, 
                                    playergamelogs,
                                    draftboard,
                                    commonteamroster,
                                    teaminfocommon)
import pandas as pd
import numpy as np
import json
import difflib
import time
import requests
from IPython.display import display

#%%

def retry(func, retries=3):
    def retry_wrapper(*args, **kwargs):
        attempts = 0
        while attempts < retries:
            try:
                return func(*args, **kwargs)
            except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
                print(f"Attempt {attempts + 1} failed: {e}")
                time.sleep(30)
                attempts += 1
        raise Exception(f"Failed after {retries} attempts")
    return retry_wrapper


# =============================================================================
# ULTRA-FAST: TeamGameLogs - ALL teams in ONE API call per season
# See: https://github.com/swar/nba_api/blob/master/docs/nba_api/stats/endpoints/teamgamelogs.md
# =============================================================================
def getTeamGameLogs(seasons, season_type='Regular Season'):
    """
    Get all team game logs using TeamGameLogs endpoint.
    ONE API call per season gets ALL 30 teams' data
    
    Args:
        seasons: List of season years (e.g., [2022, 2023] for 2022-23 and 2023-24)
        season_type: 'Regular Season', 'Playoffs', etc.
    
    Returns:
        DataFrame with all team game logs
    """
    
    @retry
    def fetch_all_team_logs(season_str, season_type):
        """Fetch ALL teams' game logs in ONE call!"""
        logs = teamgamelogs.TeamGameLogs(
            season_nullable=season_str,
            season_type_nullable=season_type
        )
        return logs.get_data_frames()[0]
    
    all_logs = []
    
    for season in seasons:
        season_str = f"{season}-{str(season + 1)[-2:]}"
        print(f"Loading Team Game Logs for {season_str} {season_type}...", end=" ")
        
        time.sleep(0.6)  # Rate limiting
        
        try:
            df = fetch_all_team_logs(season_str, season_type)
            all_logs.append(df)
            print(f"✓ {len(df)} records")
        except Exception as e:
            print(f"ERROR: {e}")
    
    # Combine all seasons
    game_logs = pd.concat(all_logs, ignore_index=True)
    
    # Parse game date
    game_logs['GAME_DATE'] = pd.to_datetime(game_logs['GAME_DATE'])
    
    # Add W column (1 for win, 0 for loss)
    game_logs['W'] = (game_logs['WL'] == 'W').astype(int)
    
    # Determine home/away from MATCHUP column
    game_logs['IS_HOME'] = game_logs['MATCHUP'].str.contains('vs.').astype(int)
    
    print(f"\n✓ Loaded {len(game_logs)} total game records")
    print(f"  Unique games: {game_logs['GAME_ID'].nunique()}")
    print(f"  Teams: {game_logs['TEAM_ID'].nunique()}")
    
    return game_logs


def getPlayerGameLogs(seasons, season_type='Regular Season'):
    """
    Get all team game logs using TeamGameLogs endpoint.
    ONE API call per season gets ALL 30 teams' data
    
    Args:
        seasons: List of season years (e.g., [2022, 2023] for 2022-23 and 2023-24)
        season_type: 'Regular Season', 'Playoffs', etc.
    
    Returns:
        DataFrame with all team game logs
    """
    
    @retry
    def fetch_all_team_logs(season_str, season_type):
        """Fetch ALL teams' game logs in ONE call!"""
        logs = playergamelogs.PlayerGameLogs(
            season_nullable=season_str,
            season_type_nullable=season_type
        )
        return logs.get_data_frames()[0]
    

    all_logs = []
    
    for season in seasons:
        season_str = f"{season}-{str(season + 1)[-2:]}"
        print(f"Loading Player Game Logs for {season_str} {season_type}...", end=" ")
        
        time.sleep(0.6)  # Rate limiting
        
        try:
            df = fetch_all_team_logs(season_str, season_type)
            all_logs.append(df)
            print(f"✓ {len(df)} records")
        except Exception as e:
            print(f"ERROR: {e}")
    
    # Combine all seasons
    game_logs = pd.concat(all_logs, ignore_index=True)
    
    # Parse game date
    game_logs['GAME_DATE'] = pd.to_datetime(game_logs['GAME_DATE'])
    
    # Add W column (1 for win, 0 for loss)
    game_logs['W'] = (game_logs['WL'] == 'W').astype(int)
    
    # Determine home/away from MATCHUP column
    game_logs['IS_HOME'] = game_logs['MATCHUP'].str.contains('vs.').astype(int)
    
    print(f"\n✓ Loaded {len(game_logs)} total game records")
    print(f"  Unique games: {game_logs['GAME_ID'].nunique()}")
    print(f"  Teams: {game_logs['TEAM_ID'].nunique()}")
    
    return game_logs

def getTeamRostersBySeason(season='2023-24'):
    """Get tean roster for a given season. Returns a dataframe with the following columns:
            ['TeamID',
            'SEASON',
            'LeagueID',
            'PLAYER',
            'NICKNAME',
            'PLAYER_SLUG',
            'NUM',
            'POSITION',
            'HEIGHT',
            'WEIGHT',
            'BIRTH_DATE',
            'AGE',
            'EXP',
            'SCHOOL',
            'PLAYER_ID',
            'team_name']
 """

    @retry
    def getTeamRoster(team_id, season, timeout = 60, headers = None):
        roster = commonteamroster.CommonTeamRoster(
            team_id=team_id, 
            season=season,
            timeout=timeout,  # Increased timeout
            headers=headers
        )
        return roster.get_data_frames()[0].drop(columns=['HOW_ACQUIRED'])

    all_teams = teams.get_teams()
    all_players = []
    missing_teams = []

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'https://www.nba.com/',
    }

    for i, team in enumerate(all_teams):
        time.sleep(1)
        try:
            df = getTeamRoster(team['id'], season, timeout = 60, headers = headers)
            df["team_name"] = team['full_name']
            if not df.empty:
                df = df.dropna(axis = 0)
                all_players.append(df)
                print(f"[{i+1}/30] {team['abbreviation']}: {len(df)} players")
                print(f"Number of rows with NA: {df.isna().any(axis=1).sum()}")
            else:
                print(f"[{i+1}/30] {team['abbreviation']}: No players found")
                missing_teams.append(team['abbreviation', season])
        except Exception as e:
            print(f"[{i+1}/30] {team['abbreviation']}: ERROR - {e}")
    
    players = pd.concat(all_players, ignore_index=True)
    players = players.drop_duplicates(subset='PLAYER_ID')  # Remove duplicates
    
    print(f"\n✓ {len(players)} unique players with birthdates")
    return players


def get_teams_info(seasons):
    @retry
    def get_team_info(team_id, season = 2025, timeout = 120, headers = None):
        info = teaminfocommon.TeamInfoCommon(
            team_id=team_id,
            timeout=timeout,
            headers=headers
        )
        return info.get_data_frames()[0][['TEAM_ID', 
                                          'TEAM_CITY', 
                                          'TEAM_NAME', 
                                          'TEAM_ABBREVIATION', 
                                          'TEAM_CONFERENCE', 
                                          'TEAM_DIVISION', 
                                          'TEAM_CODE', 
                                          'TEAM_SLUG']]

    teams_lst = teams.get_teams()
    all_teams_info = []
    for season in seasons:
        for team in teams_lst:
            time.sleep(0.6)
            try:
                print(f"Getting team info for {team['full_name']} in {season}")
                team_info = get_team_info(team['id'], season)
                all_teams_info.append(team_info)
            except Exception as e:
                print(f"Error getting team info for {team['id']} in {season}: {e}")
        
    return pd.concat(all_teams_info, ignore_index=True)


#%%

seasons_to_load = [2020 + i for i in range(1)]
team_game_logs = getTeamGameLogs(seasons_to_load, season_type='Regular Season')
player_game_logs = getPlayerGameLogs(seasons_to_load, season_type='Regular Season')
display(team_game_logs.head())

# team_game_logs.to_csv('./data/team_game_logs_2020_2025.csv', index=False)
# player_game_logs.to_csv('./data/player_game_logs_2020_2025.csv', index=False)

#%%
team_rosters_lst = []
years = [2025 + i for i in range(1)]
for year in years:
    print(f"Loading team rosters for {year}...")
    year_str = str(year) + "-" + str(year+1)[-2:]
    roster = getTeamRostersBySeason(year_str)
    print(roster.head())
    team_rosters_lst.append(roster) 

team_rosters = pd.concat(team_rosters_lst, ignore_index=True)
# team_rosters.to_csv("./data/team_rosters_2025.csv", index=False)

# %%
# WILL MOST LIKELY FAIL, HAD TO GO A ROUND ABOUT WAY TO GET DATA THAT IS IN team_info.csv

all_teams_df = get_teams_info([2025])

#%%


