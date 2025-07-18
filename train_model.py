import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import pickle
import time
import requests
from features import get_player_id, normalize_team_input
from nba_api.stats.endpoints import playergamelog

# Setup headers to avoid 403 errors from NBA API
requests.sessions.Session.headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.nba.com/'
}

# Helper to collect training data with retry
def get_player_training_rows(player_id, opponent_abbr, retries=3):
    for attempt in range(retries):
        try:
            log = playergamelog.PlayerGameLog(player_id=player_id, season='ALL', timeout=60)
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
    "Stephen Curry", "Luka Doncic", "Joel Embiid", "Jayson Tatum", "Kevin Durant",
    "De'Aaron Fox", "Jaylen Brown", "Brandon Ingram", "Jalen Brunson", "Pascal Siakam",
    "Tyrese Haliburton", "Anthony Edwards", "Jalen Green", "Paolo Banchero", "Scottie Barnes",
    "Maxi Kleber", "Aaron Gordon", "Alex Caruso", "Royce O'Neale", "Kevon Looney",
    "Georges Niang", "Dennis Smith Jr.", "T.J. McConnell", "Thaddeus Young",
    "Derrick Jones Jr.", "Tristan Vukcevic", "Kai Jones", "Ish Smith", "Sandro Mamukelashvili"
]

# Opponents to train against
teams_to_train_on = [
    "mavs", "warriors", "bucks", "sixers", "lakers", "nuggets",
    "celtics", "suns", "grizzlies", "knicks"
]

# Collect training data
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

# Train model
df = pd.DataFrame(training_data)
if df.empty:
    raise ValueError("No training data collected. Exiting.")

X = df.drop('actual_pts', axis=1)
y = df['actual_pts']

# Fit with DataFrame so that column names are preserved
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)

# Save model and feature columns together to avoid feature name warnings
with open('model.pkl', 'wb') as f:
    pickle.dump({'model': model, 'feature_names': X.columns.tolist()}, f)

print("Model trained and saved successfully.")
