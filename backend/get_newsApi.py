import requests
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("NEWS_API_KEY") 
url = f'https://newsapi.org/v2/top-headlines?country=us&apiKey={API_KEY}'


try:
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    data = response.json()

    if response.status_code == 200:
        print("Success! Here is one headline:")
        print(data['articles'][0]['title'])
    else:
        print("Error Message from API:", data.get('message', 'No message provided'))

except Exception as e:
    print(f"Connection Error: {e}")

data = response.json()
print("API Response Keys:", data.keys()) 
