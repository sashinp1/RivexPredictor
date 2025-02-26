import streamlit as st
import pandas as pd
import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
import random
from datetime import datetime, timedelta
import plotly.graph_objects as go

# Initialize VADER Analyzer
analyzer = SentimentIntensityAnalyzer()

# API-Football API Key
api_football_key = '6d2f9db7d089f603e6affbebdf27d37d'

# Top 10 leagues worldwide
league_ids = {
    'Premier League': 39,
    'La Liga': 140,
    'Serie A': 135,
    'Bundesliga': 78,
    'Ligue 1': 61,
    'MLS': 253,
    'Saudi Pro League': 307,
    'Eredivisie': 88,
    'Liga MX': 262,
    'J1 League': 98
}

# Function to fetch news related to the match
def fetch_news(query, date):
    api_key = '5672bdc979444d26a00e3bf8c670aac9'  # NewsAPI key
    url = f'https://newsapi.org/v2/everything?q={query}&from={date}&to={date}&sortBy=popularity&apiKey={api_key}'
    response = requests.get(url)
    if response.status_code == 200:
        articles = response.json()['articles']
        return articles[:5]  # Return top 5 articles
    else:
        return []

# Function to fetch historical fixtures from 2023
def fetch_historical_fixtures():
    url = "https://v3.football.api-sports.io/fixtures"
    fixtures = []

    for week_offset in range(52):
        start_date = (datetime(2023, 1, 1) + timedelta(weeks=week_offset)).strftime('%Y-%m-%d')
        end_date = (datetime(2023, 1, 1) + timedelta(weeks=week_offset + 1)).strftime('%Y-%m-%d')
        for league_name, league_id in league_ids.items():
            params = {
                'league': league_id,
                'season': 2023,
                'from': start_date,
                'to': end_date,
                'timezone': 'UTC'
            }
            headers = {
                'x-apisports-key': api_football_key,
                'Content-Type': 'application/json'
            }
            try:
                response = requests.get(url, headers=headers, params=params)
                if response.status_code == 200:
                    data = response.json()
                    if data['response']:
                        fixtures.append(random.choice(data['response']))  # Select one random trending match
            except Exception as e:
                st.error(f"Error fetching data: {e}")
    return fixtures

# Function to analyze sentiment
def analyze_sentiment(text):
    vader_sentiment = analyzer.polarity_scores(text)['compound']
    blob = TextBlob(text)
    textblob_sentiment = blob.sentiment.polarity
    return (vader_sentiment + textblob_sentiment) / 2

# Function to predict score based on sentiment and historical trends
def predict_score(home_sentiment, away_sentiment, home_team, away_team):
    base_home_goals = random.randint(0, 3)  # Base random factor for home team goals
    base_away_goals = random.randint(0, 2)  # Base random factor for away team goals

    home_score = max(0, round(base_home_goals + home_sentiment * 1.5))
    away_score = max(0, round(base_away_goals + away_sentiment * 1.5))
    
    return home_score, away_score

# Function to check if prediction was correct
def is_prediction_correct(predicted_result, actual_result):
    return predicted_result in actual_result.values()

# Function to run backtesting
def run_backtest():
    historical_fixtures = fetch_historical_fixtures()
    results = []

    for fixture in historical_fixtures:
        home_team = fixture['teams']['home']['name']
        away_team = fixture['teams']['away']['name']
        match_date = fixture['fixture']['date'][:10]
        actual_result = fixture['score']['fulltime']
        
        home_news = fetch_news(home_team, match_date)
        away_news = fetch_news(away_team, match_date)
        
        home_sentiment = sum([analyze_sentiment(article.get('description', "")) for article in home_news])
        away_sentiment = sum([analyze_sentiment(article.get('description', "")) for article in away_news])
        
        home_advantage = random.uniform(0, 0.2)
        prediction_score = home_sentiment + home_advantage - away_sentiment
        
        predicted_home_score, predicted_away_score = predict_score(home_sentiment, away_sentiment, home_team, away_team)
        
        if predicted_home_score > predicted_away_score:
            predicted_result = f"{home_team} Win"
        elif predicted_home_score < predicted_away_score:
            predicted_result = f"{away_team} Win"
        else:
            predicted_result = "Draw"
        
        correct_prediction = is_prediction_correct(predicted_result, actual_result)
        
        results.append({
            'Date': match_date,
            'Match': f"{home_team} vs {away_team}",
            'Predicted Result': predicted_result,
            'Predicted Score': f"{predicted_home_score} - {predicted_away_score}",
            'Actual Result': actual_result,
            'Correct Prediction': correct_prediction
        })
    
    return results

# Streamlit App
st.title("RivexFootyPredictor - Backtesting Mode")

if st.button("🔄 Run Backtest for 2023 Matches"):
    st.write("Fetching historical match data... This may take some time.")
    backtest_results = run_backtest()
    df = pd.DataFrame(backtest_results)
    st.dataframe(df)
    
    # Display accuracy summary
    correct_predictions = sum(1 for row in backtest_results if row['Correct Prediction'])
    total_predictions = len(backtest_results)
    accuracy = (correct_predictions / total_predictions) * 100 if total_predictions > 0 else 0
    st.write(f"✅ Backtest Accuracy: {accuracy:.2f}%")

# Note for Users
st.markdown("_This version now includes a correctness check for predicted match results._")
