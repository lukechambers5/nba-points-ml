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
    features = extract_features(player, opponent)
    if features is None:
        return "Player not found."
    prediction = model.predict(features)[0]
    return render_template('result.html', player=player, points=round(prediction, 2))

if __name__ == '__main__':
    app.run(debug=True)
