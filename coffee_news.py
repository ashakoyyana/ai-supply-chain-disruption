
import requests
import pandas as pd
from textblob import TextBlob  # Sentiment analysis library
import matplotlib.pyplot as plt

# Constants
API_KEY = "75eadfae4ea8427888c43b4e89653a2b"  # Replace with your API key
BASE_URL = "https://newsapi.org/v2/everything"

# Function to fetch news
def fetch_news(query="medicines supply chain", language="en", page_size=100):
    params = {
        "q": query,
        "language": language,
        "pageSize": page_size,  # Number of articles per request
        "apiKey": API_KEY,
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        articles = response.json().get("articles", [])
        return articles
    else:
        print(f"Error: {response.status_code}")
        return []

# Function to perform sentiment analysis
def analyze_sentiment(text):
    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity
    # Classify sentiment
    if polarity > 0:
        return "Positive"
    elif polarity < 0:
        return "Negative"
    else:
        return "Neutral"

# Main function
if __name__ == "__main__":
    # Fetch news articles
    articles = fetch_news()
    if articles:
        print("API request successful!\n")

        # Collect relevant fields and create a DataFrame
        news_data = [
            {
                "Title": article["title"],
                "Description": article["description"] or "",  # Ensure no null values
                "Source": article["source"]["name"],
                "URL": article["url"],
            }
            for article in articles
        ]
        news_df = pd.DataFrame(news_data)

        # Save raw data to CSV
        news_df.to_csv("medicines_supply_chain_news.csv", index=False)

        # Perform sentiment analysis
        print("Performing sentiment analysis...")
        news_df["Sentiment"] = news_df["Description"].apply(analyze_sentiment)

        # Save results with sentiment to CSV
        news_df.to_csv("medicines_supply_chain_news_with_sentiment.csv", index=False)

        # Display sentiment distribution
        print("\nSentiment Distribution:")
        print(news_df["Sentiment"].value_counts())

        # Plot sentiment distribution
        plt.figure(figsize=(8, 6))
        news_df["Sentiment"].value_counts().plot(kind="bar", color="skyblue")
        plt.title("Sentiment Analysis of Medicines Supply Chain News")
        plt.xlabel("Sentiment")
        plt.ylabel("Number of Articles")
        plt.show()

        # Aggregate Risk Factor
        print("\nAggregating Risk Factor...")
        risk_factor = news_df["Sentiment"].value_counts(normalize=True).get("Negative", 0) * 100
        print(f"Calculated Risk Factor from Negative Sentiment: {risk_factor:.2f}%")

    else:
        print("No articles found.")

