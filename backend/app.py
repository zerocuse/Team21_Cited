from dotenv import load_dotenv
import os
from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import spacy


load_dotenv()
app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
news_api_key = os.getenv("NEWS_API_KEY")
newsData_key = os.getenv("NEWS_DATA_API")
newsData_base_url = "https://newsdata.io/api/1/latest"
nlp = spacy.load("en_core_web_sm")


GOOGLE_API_KEY = os.getenv("GOOGLE_FACT_CHECK")
GOOGLE_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"


@app.route('/fact-check', methods=['POST'])
def handle_fact_check():
    print("Request received!") 
    query = request.form.get('query')
    
    if not query:
        return jsonify({"status": "error", "message": "No query provided"}), 400

    # 1. Use spaCy to clean/shorten the query if it's too long
    # Google API works best with concise claims (under 20 words)
    doc = nlp(query)
    sentences = [sent.text for sent in doc.sents]
    search_term = sentences[0] if sentences else query

    # 2. Call the real Google Fact Check API
    params = {
        "query": search_term,
        "key": GOOGLE_API_KEY,
        "languageCode": "en"
    }
    
    try:
        response = requests.get(GOOGLE_URL, params=params)
        response.raise_for_status() # Check for HTTP errors
        data = response.json()
        
        # 3. Extract the claims from Google's response
        # Google returns a list of 'claims', each containing 'claimReview'
        google_claims = data.get('claims', [])
        
        # 4. Structure the response for your React frontend
        results = [{
            "original_claim": search_term,
            "fact_checks": google_claims 
        }]
        
        print(f"Found {len(google_claims)} results for: {search_term}")
        return jsonify({"status": "success", "results": results})

    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500




if __name__ == "__main__":
    app.run(debug=True)