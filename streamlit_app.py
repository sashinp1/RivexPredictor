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

# Leagues for Italy, London (England), Spain, Germany, USA
league_ids = {
    'Italy': 135,
    'England': 39,
    'Spain': 140,
    'Germany': 78,
    'USA': 253
}

# Function to fetch news related to the match
def fetch_news(query):
    api_key = '5672bdc979444d26a00e3bf8c670aac9'  # NewsAPI key
    url = f'https://newsapi.org/v2/everything?q={query}&apiKey={api_key}'
    response = requests.get(url)
    if response.status_code == 200:
        articles = response.json()['articles']
        return articles[:5]  # Return top 5 articles
    else:
        return []

# Function to fetch fixtures within the next 7 days for selected leagues
def fetch_fixtures():
    url = "https://v3.football.api-sports.io/fixtures"
    end_date = (datetime.utcnow() + timedelta(days=7)).strftime('%Y-%m-%d')
    fixtures = []

    for league_name, league_id in league_ids.items():
        params = {
            'league': league_id,
            'season': datetime.utcnow().year,
            'from': datetime.utcnow().strftime('%Y-%m-%d'),
            'to': end_date,
            'timezone': 'UTC'
        }
        headers = {
            'x-apisports-key': api_football_key
        }
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            if data['response']:
                fixtures.extend(data['response'])
        elif response.status_code == 429:
            st.error("API request limit reached. Please wait or upgrade your plan.")
            return []
        else:
            st.error(f"API Error: {response.status_code} - {response.reason}")
            st.text(f"API Response: {response.text}")

    return fixtures

# Function to perform sentiment analysis using VADER and TextBlob
def analyze_sentiment(text):
    vader_sentiment = analyzer.polarity_scores(text)['compound']
    blob = TextBlob(text)
    textblob_sentiment = blob.sentiment.polarity
    combined_sentiment = (vader_sentiment + textblob_sentiment) / 2
    return combined_sentiment

# Function to create a roulette wheel
def create_roulette_wheel(matches):
    labels = [f"{m['teams']['home']['name']} vs {m['teams']['away']['name']}" for m in matches]
    fig = go.Figure(go.Pie(labels=labels, hole=0.3))
    fig.update_traces(textinfo='label+percent', pull=[0.1]*len(labels))
    return fig

# Streamlit App
st.title("RivexPredictor - AI Match Predictions (Roulette Wheel Edition)")

# Button to load top 30 fixtures
if st.button("📥 Load Top 30 Fixtures onto the Roulette Wheel"):
    fixtures = fetch_fixtures()

    if fixtures:
        fixtures = fixtures[:30]  # Limit to top 30 fixtures
        st.subheader("🎡 Spin the Roulette Wheel to Pick a Match")
        wheel_fig = create_roulette_wheel(fixtures)
        st.plotly_chart(wheel_fig)

        if st.button("🎯 Spin Roulette"):
            selected_match = random.choice(fixtures)
            home_team = selected_match['teams']['home']['name']
            away_team = selected_match['teams']['away']['name']
            match_datetime = selected_match['fixture']['date']
            match_date = datetime.strptime(match_datetime, "%Y-%m-%dT%H:%M:%S%z").astimezone(tz=timedelta(hours=-8)).date()
            match_time = datetime.strptime(match_datetime, "%Y-%m-%dT%H:%M:%S%z").astimezone(tz=timedelta(hours=-8)).time()

            st.write(f"Selected Match: **{home_team} vs {away_team}**")
            st.write(f"Match Date: **{match_date}**")
            st.write(f"Match Time: **{match_time.strftime('%H:%M')}**")

            # Fetch and Display News
            st.subheader("📰 Latest News & Pundit Reviews")
            home_news = fetch_news(home_team)
            away_news = fetch_news(away_team)

            home_sentiment = sum([analyze_sentiment(article['description'] or "") for article in home_news])
            away_sentiment = sum([analyze_sentiment(article['description'] or "") for article in away_news])

            # Prediction Logic
            st.subheader("⚽ Match Prediction")
            home_advantage = random.uniform(0, 0.2)
            prediction_score = home_sentiment + home_advantage - away_sentiment

            if prediction_score > 0.1:
                result = f"{home_team} Win"
            elif prediction_score < -0.1:
                result = f"{away_team} Win"
            else:
                result = "Draw"

            st.write(f"Predicted Outcome: **{result}**")
            st.write(f"Predicted Scoreline: {random.randint(1, 3)} - {random.randint(0, 2)}")
    else:
        st.error("No fixtures found or API limit reached.")

# Note for User
st.markdown("_This version includes a roulette wheel to pick trending matches from real-time data, with league filters and a 7-day window._")
