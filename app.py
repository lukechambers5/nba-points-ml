from flask import Flask, request, render_template
import pickle
from features import extract_features

app = Flask(__name__)
model = pickle.load(open('model.pkl', 'rb'))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    player = request.form['player']
    opponent = request.form['opponent']
    features_df = extract_features(player, opponent)
    
    if features_df is None:
        return "Player not found."
    
    prediction = model.predict(features_df)[0]
    
    # Extract original input features for display
    recent_ppg = features_df['recent_ppg'].values[0]
    career_ppg = features_df['career_ppg'].values[0]
    vs_team_ppg = features_df['vs_team_ppg'].values[0]
    
    confidence = 0.85  # temp value
    
    result = {
        'predicted_pts': round(prediction, 2),
        'recent_ppg': round(recent_ppg, 2),
        'career_ppg': round(career_ppg, 2),
        'vs_team_ppg': round(vs_team_ppg, 2),
        'confidence': confidence
    }

    return render_template('index.html', prediction=result, team=opponent)


if __name__ == '__main__':
    app.run(debug=True)
