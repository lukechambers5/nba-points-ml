from nba_api.stats.endpoints import playergamelog, commonplayerinfo
from nba_api.stats.static import players
import pandas as pd
import time
import unicodedata
from datetime import datetime


# in case user puts in different variations of team name

team_name_map = {
    "hawks": "ATL", "celtics": "BOS", "nets": "BKN", "hornets": "CHA", "bulls": "CHI",
    "cavaliers": "CLE", "mavs": "DAL", "mavericks": "DAL", "nuggets": "DEN", "pistons": "DET",
    "warriors": "GSW", "rockets": "HOU", "pacers": "IND", "clippers": "LAC", "lakers": "LAL",
    "grizzlies": "MEM", "heat": "MIA", "bucks": "MIL", "timberwolves": "MIN", "pelicans": "NOP",
    "knicks": "NYK", "thunder": "OKC", "magic": "ORL", "sixers": "PHI", "76ers": "PHI",
    "suns": "PHX", "blazers": "POR", "kings": "SAC", "spurs": "SAS", "raptors": "TOR",
    "jazz": "UTA", "wizards": "WAS"
}

def normalize_team_input(user_input):
    name = user_input.strip().lower()
    return team_name_map.get(name.upper(), team_name_map.get(name, name.upper()))

# Takes out special characters for European player names
def normalize_name(name):
    return unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8').lower()

def get_player_id(player_name):
    player_list = players.get_players()
    input_name = normalize_name(player_name)

    # Tries to match full player name
    for p in player_list:
        if normalize_name(p['full_name']) == input_name:
            return p['id']
    
    # if user doesn't put full name, then it searches for a partial match with user's name
    for p in player_list:
        if input_name in normalize_name(p['full_name']):
            return p['id']
    
    return None

# This function gets their last 5 games average points to account for a recent hot streak or slump
def get_recent_avg_pts(player_id, num_games=5):
    log = playergamelog.PlayerGameLog(player_id=player_id, season='2025')
    time.sleep(0.5)
    df = log.get_data_frames()[0]
    return df['PTS'].head(num_games).mean()

# Just gets career ppg
def get_career_ppg(player_id):
    info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
    time.sleep(0.5)
    career = info.get_data_frames()[1]
    return career['PTS'].values[0]

# Gets ppg avg vs the particular team
def get_vs_team_avg(player_id, opponent_abbr):
    log = playergamelog.PlayerGameLog(player_id=player_id, season='ALL')
    time.sleep(0.5)
    df = log.get_data_frames()[0]
    vs_df = df[df['MATCHUP'].str.contains(opponent_abbr)]
    return vs_df['PTS'].mean() if not vs_df.empty else 0

# Function that puts all the values together to send to model to train it
def extract_features(player_name, opponent_input):
    player_id = get_player_id(player_name)
    if not player_id:
        return None

    opponent_abbr = normalize_team_input(opponent_input)

    # Get core features
    recent = get_recent_avg_pts(player_id)
    career = get_career_ppg(player_id)
    vs_team = get_vs_team_avg(player_id, opponent_abbr)

    # Extra info
    info = commonplayerinfo.CommonPlayerInfo(player_id=player_id).get_data_frames()[0].iloc[0]
    time.sleep(0.5)

    birthdate_str = info.get('BIRTHDATE')
    birthdate = datetime.fromisoformat(birthdate_str) if birthdate_str else None
    age = (datetime.now() - birthdate).days // 365 if birthdate else None

    meta = {
        'full_name': info.get('DISPLAY_FIRST_LAST', 'Unknown'),
        'team': info.get('TEAM_NAME', 'Unknown'),
        'position': info.get('POSITION', 'Unknown'),
        'height': info.get('HEIGHT', 'Unknown'),
        'weight': info.get('WEIGHT', 'Unknown'),
        'age': age,
        'id': player_id
    }


    features = {
        'recent_ppg': recent,
        'career_ppg': career,
        'vs_team_ppg': vs_team,
    }

    return {
        'features': pd.DataFrame([features]),
        'meta': meta
    }