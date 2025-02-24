import streamlit as st
import pandas as pd
import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
import random

# Initialize VADER Analyzer
analyzer = SentimentIntensityAnalyzer()

# Function to fetch news related to the match
def fetch_news(query):
    api_key = 'YOUR_NEWSAPI_KEY'  # Replace with your NewsAPI key
    url = f'https://newsapi.org/v2/everything?q={query}&apiKey={api_key}'
    response = requests.get(url)
    if response.status_code == 200:
        articles = response.json()['articles']
        return articles[:5]  # Return top 5 articles
    else:
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

# Streamlit App
st.title("RivexPredictor - AI Match Predictions (VADER + TextBlob)")

# Team Selection
teams = ["Manchester City", "Arsenal", "Liverpool", "Chelsea", "Manchester United", "Tottenham"]
home_team = st.selectbox("Select Home Team", teams)
away_team = st.selectbox("Select Away Team", [team for team in teams if team != home_team])

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
if st.button("Predict Match Outcome"):
    # Basic weight between sentiment and random factor
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

# Note for User
st.markdown("_This version combines VADER and TextBlob sentiment analysis for more accurate football predictions._")
