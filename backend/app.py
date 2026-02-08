from dotenv import load_dotenv
import os
from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
from werkzeug.utils import secure_filename
from extract_files import extract_text
import certifi



load_dotenv()
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
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
        response = requests.get(
    newsData_base_url,
    params=params,
    headers=headers,
    verify=certifi.where()
)
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

    # Secure the filename before saving
    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    try:
        extracted_content = extract_text(file_path)
        if os.path.exists(file_path):
            os.remove(file_path)

        return jsonify({
            "message": "Success",
            "fileName": filename,
            "extractedText": extracted_content
        })
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)