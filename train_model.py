import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import pickle
import time
import requests
from features import get_player_id, normalize_team_input
from nba_api.stats.endpoints import playergamelog

requests.sessions.Session.headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.nba.com/'
}

# Helper to collect training data with retry
def get_player_training_rows(player_id, opponent_abbr, retries=3):
    for attempt in range(retries):
        try:
            log = playergamelog.PlayerGameLog(player_id=player_id, season='2023', timeout=60)
            df = log.get_data_frames()[0]
            break
        except Exception as e:
            print(f"Error fetching player ID {player_id} (attempt {attempt + 1}): {e}")
            time.sleep(3)
    else:
        print(f"Failed to fetch player ID {player_id} after {retries} attempts")
        return []

    df['PTS'] = pd.to_numeric(df['PTS'], errors='coerce')
    if df.empty or len(df) < 6:
        return []

    rows = []
    for i in range(5, len(df)):
        prev_5 = df.iloc[i-5:i]
        game = df.iloc[i]

        # Match only if opponent is in the matchup
        if opponent_abbr not in game['MATCHUP']:
            continue

        recent_ppg = prev_5['PTS'].mean()
        career_ppg = df['PTS'].mean()

        vs_team_df = df[df['MATCHUP'].str.contains(opponent_abbr)]
        vs_team_ppg = vs_team_df['PTS'].mean() if not vs_team_df.empty else 0

        row = {
            'recent_ppg': recent_ppg,
            'career_ppg': career_ppg,
            'vs_team_ppg': vs_team_ppg,
            'actual_pts': game['PTS']
        }
        rows.append(row)

    return rows


# Players to train on
players_to_train_on = [
    "Luka Doncic", "Stephen Curry", "LeBron James", "Jayson Tatum", "Joel Embiid",
    "Nikola Jokic", "Devin Booker", "Jimmy Butler", "Anthony Edwards", "Damian Lillard",
    "Jamal Murray", "Trae Young", "Donovan Mitchell", "Ja Morant", "Klay Thompson"
]

# Opponents to train against (use full team names or other shortened names)
teams_to_train_on = [
    "mavs", "warriors", "bucks", "sixers", "lakers", "nuggets",
    "celtics", "suns", "grizzlies", "knicks"
]

training_data = []
for player_name in players_to_train_on:
    pid = get_player_id(player_name)
    if not pid:
        continue
    for team_name in teams_to_train_on:
        abbr = normalize_team_input(team_name)
        rows = get_player_training_rows(pid, abbr)
        training_data.extend(rows)
        time.sleep(1)

# Trains model
df = pd.DataFrame(training_data)
X = df.drop('actual_pts', axis=1)
y = df['actual_pts']

model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)

# Saves model
with open('model.pkl', 'wb') as f:
    pickle.dump(model, f)

print("Model trained successfully")
