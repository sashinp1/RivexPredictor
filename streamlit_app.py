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

# Football-Data.org API Key
football_data_api_key = '2292620df705473dbddfbbb00505969b'

# Top 10 leagues worldwide (Football-Data.org league codes)
league_codes = {
    'Premier League': 'PL',
    'La Liga': 'PD',
    'Serie A': 'SA',
    'Bundesliga': 'BL1',
    'Ligue 1': 'FL1',
    'MLS': 'MLS',
    'Eredivisie': 'DED',
    'Liga MX': 'LMX',
    'J1 League': 'J1',
    'Champions League': 'CL'
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

# Function to fetch fixtures within the next 10 days for selected leagues
def fetch_fixtures():
    url = "https://api.football-data.org/v4/matches"
    start_date = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')  # Start from yesterday
    end_date = (datetime.utcnow() + timedelta(days=10)).strftime('%Y-%m-%d')  # Extend to 10 days ahead
    fixtures = []

    headers = {
        'X-Auth-Token': football_data_api_key,
        'Content-Type': 'application/json'
    }

    for league_name, league_code in league_codes.items():
        params = {
            'competitions': league_code,
            'dateFrom': start_date,
            'dateTo': end_date
        }
        try:
            response = requests.get(url, headers=headers, params=params)
            st.text(f"API Response for {league_name}: {response.text}")

            if response.status_code == 200:
                data = response.json()
                if 'matches' in data and data['matches']:
                    fixtures.extend(data['matches'])
                else:
                    st.warning(f"No fixtures found for {league_name}. Verify league code and timeframe.")
            elif response.status_code == 401:
                st.error("Unauthorized access. Check API key.")
                return []
            else:
                st.error(f"API Error: {response.status_code} - {response.reason}")
                st.text(f"API Response: {response.text}")
        except Exception as e:
            st.error(f"An error occurred: {e}")

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
    labels = [f"{m['homeTeam']['name']} vs {m['awayTeam']['name']}" for m in matches[:10]]  # Limit to top 10
    fig = go.Figure(go.Pie(labels=labels, hole=0.3))
    fig.update_traces(textinfo='label+percent', pull=[0.1]*len(labels))
    return fig

# Function to get top 10 trending fixtures based on sentiment (headline-based)
def get_top_trending_fixtures(fixtures):
    scored_fixtures = []

    for fixture in fixtures:
        home_team = fixture['homeTeam']['name']
        away_team = fixture['awayTeam']['name']
        combined_news = fetch_news(home_team) + fetch_news(away_team)
        sentiment_score = sum([analyze_sentiment(article.get('title', "")) for article in combined_news])
        scored_fixtures.append((fixture, sentiment_score))

    # Sort by sentiment score (descending)
    scored_fixtures.sort(key=lambda x: x[1], reverse=True)
    top_fixtures = [f[0] for f in scored_fixtures[:10]]

    return top_fixtures

# Streamlit App
st.title("RivexFootyPredictor - Global Top 10 Trending Matches Edition (Football-Data.org)")

# Load and display top 10 trending matches
if st.button("📊 Show Top 10 Trending Games Worldwide"):
    fixtures = fetch_fixtures()

    if fixtures:
        trending_fixtures = get_top_trending_fixtures(fixtures)
        st.subheader("🔥 Top 10 Trending Matches:")
        for i, fixture in enumerate(trending_fixtures, 1):
            home_team = fixture['homeTeam']['name']
            away_team = fixture['awayTeam']['name']
            match_date = fixture['utcDate'][:10]
            st.write(f"{i}. {home_team} vs {away_team} - {match_date}")

        # Load into Roulette Wheel
        if st.button("🎡 Spin Roulette to Pick a Match"):
            wheel_fig = create_roulette_wheel(trending_fixtures)
            st.plotly_chart(wheel_fig)

            # Randomly select a match after spin
            selected_match = random.choice(trending_fixtures)
            home_team = selected_match['homeTeam']['name']
            away_team = selected_match['awayTeam']['name']
            match_datetime = selected_match['utcDate']

            # Display Selected Match
            st.write(f"🎯 Selected Match: {home_team} vs {away_team} on {match_datetime}")

            # Fetch Detailed News After Selection
            home_news = fetch_news(home_team)
            away_news = fetch_news(away_team)

            home_sentiment = sum([analyze_sentiment(article.get('description', "")) for article in home_news])
            away_sentiment = sum([analyze_sentiment(article.get('description', "")) for article in away_news])

            home_advantage = random.uniform(0, 0.2)
            prediction_score = home_sentiment + home_advantage - away_sentiment

            # Finally, highlight the predicted outcome
            st.subheader("🔮 Predicted Outcome")
            if prediction_score > 0.1:
                result = f"{home_team} Win"
            elif prediction_score < -0.1:
                result = f"{away_team} Win"
            else:
                result = "Draw"

            st.write(f"**Predicted Result:** {result}")
            st.write(f"**Predicted Scoreline:** {random.randint(1, 3)} - {random.randint(0, 2)}")

# Note for Users
st.markdown("_This version now uses Football-Data.org API instead of API-Football._")
