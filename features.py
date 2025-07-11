from nba_api.stats.endpoints import playergamelog, commonplayerinfo
from nba_api.stats.static import players
import pandas as pd
import unicodedata
from datetime import datetime
import requests
from nba_api.stats.library.http import NBAStatsHTTP

NBAStatsHTTP._session = requests.Session()
NBAStatsHTTP._session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Origin': 'https://www.nba.com',
    'Referer': 'https://www.nba.com/',
    'x-nba-stats-origin': 'stats',
    'x-nba-stats-token': 'true'
})

# Cache API responses in memory
CACHE = {
    "players": players.get_players(),
    "logs": {},
    "common_info": {}
}

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
            log = playergamelog.PlayerGameLog(player_id=player_id, season='2023', timeout=5)
            CACHE["logs"][player_id] = log.get_data_frames()[0]
        df = CACHE["logs"][player_id]
        return df['PTS'].head(num_games).mean()
    except Exception as e:
        return 0

def get_career_ppg(player_id):
    try:
        if player_id not in CACHE["common_info"]:
            info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
            CACHE["common_info"][player_id] = info.get_data_frames()
        frames = CACHE["common_info"][player_id]
        career_df = frames[1] if len(frames) > 1 else pd.DataFrame()
        return career_df['PTS'].values[0] if not career_df.empty else 0
    except Exception as e:
        return 0



def get_vs_team_avg(player_id, opponent_abbr):
    try:
        if player_id not in CACHE["logs"]:
            log = playergamelog.PlayerGameLog(player_id=player_id, season='2023', timeout=5)
            CACHE["logs"][player_id] = log.get_data_frames()[0]
        df = CACHE["logs"][player_id]

        # Normalize MATCHUP
        df['MATCHUP'] = df['MATCHUP'].str.strip().str.upper()

        # Filter rows
        vs_df = df[df['MATCHUP'].str.contains(opponent_abbr.upper(), na=False)]
        return vs_df['PTS'].mean() if not vs_df.empty else 0
    except Exception as e:
        return 0


def extract_features(player_name, opponent_input):
    player_id = get_player_id(player_name)
    if not player_id:
        return None

    opponent_abbr = normalize_team_input(opponent_input)

    try:
        recent = get_recent_avg_pts(player_id)
    except Exception as e:
        return None

    try:
        career = get_career_ppg(player_id)
    except Exception as e:
        return None

    try:
        vs_team = get_vs_team_avg(player_id, opponent_abbr)
    except Exception as e:
        return None

    try:
        if player_id not in CACHE["common_info"]:
            info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
            CACHE["common_info"][player_id] = info.get_data_frames()

        bio_df = CACHE["common_info"][player_id][0]

        if bio_df.empty:
            return None

        info_row = bio_df.iloc[0]
    except Exception as e:
        import traceback
        return None


    birthdate_str = info_row['BIRTHDATE'] if 'BIRTHDATE' in bio_df.columns else None

    try:
        birthdate = datetime.fromisoformat(birthdate_str) if birthdate_str else None
        age = (datetime.now() - birthdate).days // 365 if birthdate else None
    except:
        age = None

    meta = {
        'full_name': info_row.get('DISPLAY_FIRST_LAST', 'Unknown') if isinstance(info_row, dict) else info_row.get('DISPLAY_FIRST_LAST', 'Unknown') if 'DISPLAY_FIRST_LAST' in info_row else 'Unknown',
        'team': info_row.get('TEAM_NAME', 'Unknown') if 'TEAM_NAME' in info_row else 'Unknown',
        'position': info_row.get('POSITION', 'Unknown') if 'POSITION' in info_row else 'Unknown',
        'height': info_row.get('HEIGHT', 'Unknown') if 'HEIGHT' in info_row else 'Unknown',
        'weight': info_row.get('WEIGHT', 'Unknown') if 'WEIGHT' in info_row else 'Unknown',
        'age': age,
        'id': player_id
    }


    features = {
        'recent_ppg': recent,
        'career_ppg': career,
        'vs_team_ppg': vs_team,
    }

    try:
        df = pd.DataFrame([features])
        return {
            'features': df,
            'meta': meta
        }
    except Exception as e:
        import traceback
        return None

