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
    url = "https://v3.football.api-sports.io/fixtures"
    start_date = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')  # Start from yesterday
    end_date = (datetime.utcnow() + timedelta(days=10)).strftime('%Y-%m-%d')  # Extend to 10 days ahead
    fixtures = []

    for league_name, league_id in league_ids.items():
        params = {
            'league': league_id,
            'season': datetime.utcnow().year,  # Verify if this season year is correct
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

            # Debug: Print the full API response
            st.text(f"API Response for {league_name}: {response.text}")

            if response.status_code == 200:
                data = response.json()
                if data['response']:
                    fixtures.extend(data['response'])
                else:
                    st.warning(f"No fixtures found for {league_name}. Verify league ID and season.")
            elif response.status_code == 401:
                st.error("Unauthorized access. Check API key.")
                return []
            elif response.status_code == 429:
                st.error("API request limit reached. Please wait or upgrade your plan.")
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
    labels = [f"{m['teams']['home']['name']} vs {m['teams']['away']['name']}" for m in matches[:10]]  # Limit to top 10
    fig = go.Figure(go.Pie(labels=labels, hole=0.3))
    fig.update_traces(textinfo='label+percent', pull=[0.1]*len(labels))
    return fig

# Function to get top 10 trending fixtures based on sentiment (headline-based)
def get_top_trending_fixtures(fixtures):
    scored_fixtures = []

    for fixture in fixtures:
        home_team = fixture['teams']['home']['name']
        away_team = fixture['teams']['away']['name']
        combined_news = fetch_news(home_team) + fetch_news(away_team)
        sentiment_score = sum([analyze_sentiment(article.get('title', "")) for article in combined_news])
        scored_fixtures.append((fixture, sentiment_score))

    # Sort by sentiment score (descending)
    scored_fixtures.sort(key=lambda x: x[1], reverse=True)
    top_fixtures = [f[0] for f in scored_fixtures[:10]]

    return top_fixtures

# Streamlit App
st.title("RivexFootyPredictor - Global Top 10 Trending Matches Edition")

# Load and display top 10 trending matches
if st.button("📊 Show Top 10 Trending Games Worldwide"):
    fixtures = fetch_fixtures()

    if fixtures:
        trending_fixtures = get_top_trending_fixtures(fixtures)
        st.subheader("🔥 Top 10 Trending Matches:")
        for i, fixture in enumerate(trending_fixtures, 1):
            home_team = fixture['teams']['home']['name']
            away_team = fixture['teams']['away']['name']
            match_date = fixture['fixture']['date'][:10]
            st.write(f"{i}. {home_team} vs {away_team} - {match_date}")

        # Load into Roulette Wheel
        if st.button("🎡 Spin Roulette to Pick a Match"):
            wheel_fig = create_roulette_wheel(trending_fixtures)
            st.plotly_chart(wheel_fig)

            # Randomly select a match after spin
            selected_match = random.choice(trending_fixtures)
            home_team = selected_match['teams']['home']['name']
            away_team = selected_match['teams']['away']['name']
            match_datetime = selected_match['fixture']['date']

            # Display Selected Match
            st.write(f"🎯 Selected Match: {home_team} vs {away_team} on {match_datetime}")

            # Fetch Detailed News After Selection
            home_news = fetch_news(home_team)
            away_news = fetch_news(away_team)

            home_sentiment = sum([analyze_sentiment(article.get('description', "")) for article in home_news])
            away_sentiment = sum([analyze_sentiment(article.get('description', "")) for article in away_news])

            home_advantage = random.uniform(0, 0.2)
            prediction_score = home_sentiment + home_advantage - away_sentiment

            # Display Key Players
            st.subheader("⚽ Key Players to Watch")
            st.write(f"**{home_team} Key Players:**")
            for player in [article['title'] for article in home_news][:3]:
                st.write(f"- {player}")

            st.write(f"**{away_team} Key Players:**")
            for player in [article['title'] for article in away_news][:3]:
                st.write(f"- {player}")

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
# st.markdown("_This version adds API response debugging and verifies the season parameter._")
