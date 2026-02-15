# Test script to verify NewsAPI connection
import requests
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("NEWS_API_KEY") 

def test_news_api_connection():
    url = f'https://newsapi.org/v2/top-headlines?country=us&apiKey={API_KEY}'
    response = requests.get(url)
    
    assert response.status_code == 200
    data = response.json()
    print("✓ NewsAPI connected successfully")
    print(f"Sample headline: {data['articles'][0]['title']}")

if __name__ == "__main__":
    test_news_api_connection()