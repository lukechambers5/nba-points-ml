import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import pickle
import time
from features import get_player_id, get_player_id, normalize_name
from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog

# Helper to collect training data
def get_player_training_rows(player_id, team_abbr):
    log = playergamelog.PlayerGameLog(player_id=player_id, season='2023')
    df = log.get_data_frames()[0]
    df['PTS'] = pd.to_numeric(df['PTS'])

    if df.empty or len(df) < 6:
        return []

    rows = []
    for i in range(5, len(df)):
        prev_5 = df.iloc[i-5:i]
        game = df.iloc[i]

        recent_ppg = prev_5['PTS'].mean()
        career_ppg = df['PTS'].mean()
        vs_team_df = df[df['MATCHUP'].str.contains(team_abbr)]
        vs_team_ppg = vs_team_df['PTS'].mean() if not vs_team_df.empty else 0

        if team_abbr not in game['MATCHUP']:
            continue

        row = {
            'recent_ppg': recent_ppg,
            'career_ppg': career_ppg,
            'vs_team_ppg': vs_team_ppg,
            'actual_pts': game['PTS']
        }
        rows.append(row)

    return rows

# Train on multiple players
players_to_train_on = ['Luka Doncic', 'Stephen Curry', 'LeBron James', 'Jayson Tatum', 'Kevin Durant']
teams = ['LAL', 'PHX', 'GSW', 'BOS', 'DAL']

training_data = []
for name in players_to_train_on:
    pid = get_player_id(name)
    if not pid:
        continue
    for team in teams:
        rows = get_player_training_rows(pid, team)
        training_data.extend(rows)
        time.sleep(1)

# Build DataFrame and model
df = pd.DataFrame(training_data)
X = df.drop('actual_pts', axis=1)
y = df['actual_pts']

model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)

with open('model.pkl', 'wb') as f:
    pickle.dump(model, f)

print("✅ Model trained on real NBA game data!")
