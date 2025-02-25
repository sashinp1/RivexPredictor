import streamlit as st
import pandas as pd
import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
import random
from datetime import datetime, timedelta

# Initialize VADER Analyzer
analyzer = SentimentIntensityAnalyzer()

# API-Football API Key
api_football_key = '6d2f9db7d089f603e6affbebdf27d37d'

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

# Function to fetch real-time fixtures from API-Football with error handling
def fetch_fixtures():
    url = "https://v3.football.api-sports.io/fixtures"
    params = {
        'next': 10,  # Fetch next 10 fixtures
        'timezone': 'Europe/London'  # Ensure timezone compatibility
    }
    headers = {
        'x-apisports-key': api_football_key
    }
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        if data['response']:
            return data['response']
        else:
            st.error("No fixtures available. Try again later.")
            return []
    elif response.status_code == 429:
        st.error("API request limit reached. Please wait or upgrade your plan.")
        return []
    else:
        st.error(f"API Error: {response.status_code} - {response.reason}")
        return []

# Function to perform sentiment analysis using VADER and TextBlob
def analyze_sentiment(text):
    # VADER Sentiment
    vader_sentiment = analyzer.polarity_scores(text)['compound']

    # TextBlob Sentiment
    blob = TextBlob(text)
    textblob_sentiment = blob.sentiment.polarity

    # Combine both scores (average)
    combined_sentiment = (vader_sentiment + textblob_sentiment) / 2

    return combined_sentiment

# Function to select the most exciting upcoming match
def select_exciting_match(fixtures):
    match_scores = {}
    for fixture in fixtures:
        home_team = fixture['teams']['home']['name']
        away_team = fixture['teams']['away']['name']
        home_news = fetch_news(home_team)
        away_news = fetch_news(away_team)

        home_sentiment = sum([analyze_sentiment(article['description'] or "") for article in home_news])
        away_sentiment = sum([analyze_sentiment(article['description'] or "") for article in away_news])

        excitement_score = abs(home_sentiment) + abs(away_sentiment)
        match_scores[(home_team, away_team, fixture['fixture']['date'])] = excitement_score

    if match_scores:
        most_exciting_match = max(match_scores, key=match_scores.get)
        return most_exciting_match
    else:
        st.error("No exciting matches found.")
        return None

# Streamlit App
st.title("RivexPredictor - AI Match Predictions (Real-Time Fixtures)")

if st.button("Pick Most Exciting Match"):
    fixtures = fetch_fixtures()
    if fixtures:
        selected_match = select_exciting_match(fixtures)
        if selected_match:
            home_team, away_team, match_datetime = selected_match
            match_date = datetime.strptime(match_datetime, "%Y-%m-%dT%H:%M:%S%z").date()
            match_time = datetime.strptime(match_datetime, "%Y-%m-%dT%H:%M:%S%z").time()

            st.write(f"Selected Match: **{home_team} vs {away_team}**")
            st.write(f"Match Date: **{match_date}**")
            st.write(f"Match Time: **{match_time.strftime('%H:%M')}**")

            # Fetch and Display News
            st.subheader("📰 Latest News & Pundit Reviews")
            home_news = fetch_news(home_team)
            away_news = fetch_news(away_team)

            home_sentiment = 0
            away_sentiment = 0

            if home_news:
                st.write(f"**{home_team} News:**")
                for article in home_news:
                    st.write(f"- [{article['title']}]({article['url']})")
                    home_sentiment += analyze_sentiment(article['description'] or "")
            else:
                st.write(f"No recent news found for {home_team}.")

            if away_news:
                st.write(f"**{away_team} News:**")
                for article in away_news:
                    st.write(f"- [{article['title']}]({article['url']})")
                    away_sentiment += analyze_sentiment(article['description'] or "")
            else:
                st.write(f"No recent news found for {away_team}.")

            # Average Sentiment
            home_sentiment /= max(len(home_news), 1)
            away_sentiment /= max(len(away_news), 1)

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
        st.error("No upcoming fixtures found or API limit reached.")

# Note for User
st.markdown("_This version integrates real-time match fixtures from API-Football and includes enhanced sentiment analysis with error handling._")
