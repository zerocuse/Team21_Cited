import requests
from config import Config

class KnowledgeBase:
    def __init__(self):
        self.news_api_key = Config.NEWS_API_KEY
        self.news_base_url = "https://newsapi.org/v2"
    
    def search(self, query, max_results=5):
        """Search multiple knowledge sources for a claim"""
        results = []
        results.extend(self._search_news(query, max_results=3))
        return results[:max_results]
    
    def _search_news(self, query, max_results=3):
        """
        Search news articles by query (not just top headlines)
        This is what you need for fact-checking!
        """
        url = f"{self.news_base_url}/everything"  
        params = {
            'q': query,
            'apiKey': self.news_api_key,
            'pageSize': max_results,
            'sortBy': 'relevancy', 
            'language': 'en'
        }
        
        try:
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                
                return [{
                    'url': article['url'],
                    'title': article['title'],
                    'snippet': article.get('description', ''),
                    'source': article['source']['name'],
                    'published_at': article['publishedAt'],
                    'source_type': 'news'
                } for article in articles]
            else:
                print(f"NewsAPI Error: {response.status_code} - {data.get('message')}")
                return []
                
        except Exception as e:
            print(f"NewsAPI Connection Error: {e}")
            return []
    
    def get_top_headlines(self, country='us'):
        """
        Optional: Get top headlines for general news browsing
        (Not needed for fact-checking, but useful for context)
        """
        url = f"{self.news_base_url}/top-headlines"
        params = {
            'country': country,
            'apiKey': self.news_api_key
        }
        
        response = requests.get(url, params=params)
        return response.json().get('articles', [])