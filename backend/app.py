
from dotenv import load_dotenv
import os
from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
from werkzeug.utils import secure_filename
from extract_files import extract_text



load_dotenv()
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})
news_api_key = os.getenv("NEWS_API_KEY")
newsData_key = os.getenv("NEWS_DATA_API")
newsData_base_url = "https://newsdata.io/api/1/latest"
@app.route("/api/newsdata")
def newsdata():
    search = request.args.get("search", "").lower()

    params = {
        "apikey": newsData_key,
        "language": "en",
        "q": "breaking,politics",
        "country": "us"
    }

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(newsData_base_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json().get("results", [])

        if search:
            data = [
                item for item in data
                if search in (item.get("title") or "").lower()
                or search in (item.get("description") or "").lower()
            ]

        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    


UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/api/upload", methods=["POST"])
def handle_upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # 1. Save file temporarily
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    try:
        # 2. Use your existing Python function
        extracted_content = extract_text(file_path)
        
        # 3. Clean up (optional: delete file after extraction)
        os.remove(file_path)

        # 4. Return the text to React
        return jsonify({
            "message": "Success",
            "fileName": file.filename,
            "extractedText": extracted_content
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    if not newsData_key:
        print("WARNING: NEWS_DATA_API key not found in .env file!")
    
    app.run(debug=True)