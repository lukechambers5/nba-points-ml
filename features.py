from nba_api.stats.endpoints import playergamelog, commonplayerinfo
from nba_api.stats.static import players
import pandas as pd
import time
import unicodedata

def normalize_name(name):
    return unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8').lower()

def get_player_id(player_name):
    player_list = players.get_players()
    input_name = normalize_name(player_name)

    # Try exact match first
    for p in player_list:
        if normalize_name(p['full_name']) == input_name:
            return p['id']
    
    # Try partial match
    for p in player_list:
        if input_name in normalize_name(p['full_name']):
            return p['id']
    
    return None

def get_recent_avg_pts(player_id, num_games=5):
    log = playergamelog.PlayerGameLog(player_id=player_id, season='2023')
    time.sleep(0.5)
    df = log.get_data_frames()[0]
    return df['PTS'].head(num_games).mean()

def get_career_ppg(player_id):
    info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
    time.sleep(0.5)
    career = info.get_data_frames()[1]
    return career['PTS'].values[0]

def get_vs_team_avg(player_id, opponent_abbr):
    log = playergamelog.PlayerGameLog(player_id=player_id, season='2023')
    time.sleep(0.5)
    df = log.get_data_frames()[0]
    vs_df = df[df['MATCHUP'].str.contains(opponent_abbr)]
    return vs_df['PTS'].mean() if not vs_df.empty else 0

def extract_features(player_name, opponent_abbr):
    player_id = get_player_id(player_name)
    if not player_id:
        return None
    features = {
        'recent_ppg': get_recent_avg_pts(player_id),
        'career_ppg': get_career_ppg(player_id),
        'vs_team_ppg': get_vs_team_avg(player_id, opponent_abbr)
    }
    return pd.DataFrame([features])
