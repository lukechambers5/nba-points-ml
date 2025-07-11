from nba_api.stats.endpoints import playergamelog, commonplayerinfo
from nba_api.stats.static import players
import pandas as pd
import unicodedata
from datetime import datetime

# Cache API responses in memory
CACHE = {
    "players": players.get_players(),
    "logs": {},         # player_id -> DataFrame
    "common_info": {}   # player_id -> (bio_df, career_df)
}

team_name_map = {
    # Add all nicknames here as before...
    "mavs": "DAL", "mavericks": "DAL", "dallas": "DAL", "dal": "DAL", "dallas mavericks": "DAL",
    # (Repeat for all other teams as shown previously)
}

def normalize_team_input(user_input):
    name = user_input.strip().lower()
    return team_name_map.get(name, name.upper())

def normalize_name(name):
    return unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8').lower()

def get_player_id(player_name):
    input_name = normalize_name(player_name)
    for p in CACHE["players"]:
        if normalize_name(p['full_name']) == input_name:
            return p['id']
    for p in CACHE["players"]:
        if input_name in normalize_name(p['full_name']):
            return p['id']
    return None

def get_recent_avg_pts(player_id, num_games=5):
    try:
        if player_id not in CACHE["logs"]:
            log = playergamelog.PlayerGameLog(player_id=player_id, season='2025', timeout=5)
            CACHE["logs"][player_id] = log.get_data_frames()[0]
        df = CACHE["logs"][player_id]
        return df['PTS'].head(num_games).mean()
    except Exception as e:
        print(f"[get_recent_avg_pts] Error: {e}")
        return 0

def get_career_ppg(player_id):
    try:
        if player_id not in CACHE["common_info"]:
            info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
            CACHE["common_info"][player_id] = info.get_data_frames()
        _, career_df = CACHE["common_info"][player_id]
        return career_df['PTS'].values[0]
    except Exception as e:
        print(f"[get_career_ppg] Error: {e}")
        return 0

def get_vs_team_avg(player_id, opponent_abbr):
    try:
        if player_id not in CACHE["logs"]:
            log = playergamelog.PlayerGameLog(player_id=player_id, season='2025', timeout=5)
            CACHE["logs"][player_id] = log.get_data_frames()[0]
        df = CACHE["logs"][player_id]
        vs_df = df[df['MATCHUP'].str.contains(opponent_abbr)]
        return vs_df['PTS'].mean() if not vs_df.empty else 0
    except Exception as e:
        print(f"[get_vs_team_avg] Error: {e}")
        return 0

def extract_features(player_name, opponent_input):
    player_id = get_player_id(player_name)
    if not player_id:
        return None

    opponent_abbr = normalize_team_input(opponent_input)

    recent = get_recent_avg_pts(player_id)
    career = get_career_ppg(player_id)
    vs_team = get_vs_team_avg(player_id, opponent_abbr)

    try:
        if player_id not in CACHE["common_info"]:
            info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
            CACHE["common_info"][player_id] = info.get_data_frames()
        bio_df, _ = CACHE["common_info"][player_id]
        info = bio_df.iloc[0]
    except Exception as e:
        print(f"[extract_features] Error fetching metadata: {e}")
        info = {}

    birthdate_str = info.get('BIRTHDATE') if info else None
    try:
        birthdate = datetime.fromisoformat(birthdate_str) if birthdate_str else None
        age = (datetime.now() - birthdate).days // 365 if birthdate else None
    except:
        age = None

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
