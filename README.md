# NBA Player Points Predictor

**[Live Site](https://nba-points-predictor.fly.dev/)**

NBA Player Points Predictor is a web app that lets you **predict how many points an NBA player will score** in an upcoming game. It uses real-time data from the NBA API along with a machine learning model trained on past performance.

---

## Features

- 📊 **Point Prediction Model**
  - Predicts based on:
    - Recent 5-game average
    - Career points per game
    - Historical performance vs opponent

- 🧠 **ML-Powered Insights**
  - Uses a trained Random Forest model
  - Displays predicted points, context stats, and confidence score

- 🔍 **Live NBA Data**
  - Pulls player and game logs using `nba_api`
  - Automatically handles name matching and team abbreviation logic

- 💻 **Interactive Web Form**
  - Enter a player and an opponent team
  - See instant predictions with no login required

---

## ⚙️ Built With

- Python 3
- Flask (for web framework)
- scikit-learn (for the ML model)
- nba_api (for player data)
- pandas, requests
- HTML/CSS (basic frontend layout)

---

## 🛠️ Setup & Run

```bash
git clone https://github.com/lukechambers5/nba-points-ml.git
cd nba-points-ml
pip install -r requirements.txt
python train_model.py     # Optional: retrain model
python app.py             # Run the web server
(Open your browser and go to http://127.0.0.1:5000)
