from flask import Flask, request, render_template
import pickle
from features import extract_features
import numpy as np
import pandas as pd

app = Flask(__name__)

# Load model and feature names
with open('model.pkl', 'rb') as f:
    model_data = pickle.load(f)
    model = model_data['model']
    feature_names = model_data['feature_names']

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    player = request.form['player']
    opponent = request.form['opponent']

    try:
        result_data = extract_features(player, opponent)
        if result_data is None:
            return render_template('not_found.html', player=player)
    except Exception as e:
        return render_template('error.html', message="The NBA data couldn't be fetched. Try again.")

    features_df = result_data['features']
    meta = result_data['meta']

    # Align features with training column order
    try:
        input_df = features_df[feature_names]
    except KeyError as e:
        return f"Missing feature(s): {e}"

    prediction = model.predict(input_df)[0]
    input_array = input_df.values  # <-- Convert to plain NumPy array
    all_preds = [tree.predict(input_array)[0] for tree in model.estimators_]
    std_dev = np.std(all_preds)
    confidence = max(0.0, min(1.0, 1.0 - std_dev / 10))

    result = {
        'predicted_pts': round(prediction, 1),
        'recent_ppg': round(features_df['recent_ppg'].iloc[0], 2),
        'career_ppg': round(features_df['career_ppg'].iloc[0], 2),
        'vs_team_ppg': round(features_df['vs_team_ppg'].iloc[0], 2),
        'confidence': round(confidence, 2),
        'player': meta['full_name'],
        'team_name': meta['team'],
        'position': meta['position'],
        'height': meta['height'],
        'weight': meta['weight'],
        'age': meta['age'],
        'headshot_url': f"https://cdn.nba.com/headshots/nba/latest/1040x760/{meta['id']}.png"
    }

    return render_template('index.html', prediction=result, team=opponent)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
