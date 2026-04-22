import pytest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from routes.claim_results import claim_results_bp
from flask import Flask

@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(claim_results_bp)
    app.config['TESTING'] = True
    return app.test_client()

def test_diversity_single_source_biased(client):
    with patch('routes.claim_results.db') as mock_db, \
         patch('routes.claim_results.SourceDiversityAnalyzer') as mock_analyzer:
        mock_db.session.get.return_value = MagicMock()
        mock_analyzer.return_value.generate_diversity_report.return_value = {
            "diversity_score": 0,
            "is_single_source_biased": True,
            "recommendations": ["academic"]
        }
        res = client.get('/api/claim/abc/diversity')
        data = res.get_json()
        assert data['is_single_source_biased'] == True

def test_diversity_not_biased(client):
    with patch('routes.claim_results.db') as mock_db, \
         patch('routes.claim_results.SourceDiversityAnalyzer') as mock_analyzer:
        mock_db.session.get.return_value = MagicMock()
        mock_analyzer.return_value.generate_diversity_report.return_value = {
            "diversity_score": 80,
            "is_single_source_biased": False,
            "recommendations": []
        }
        res = client.get('/api/claim/abc/diversity')
        data = res.get_json()
        assert data['is_single_source_biased'] == False

def test_diversity_missing_claim_returns_safe_response(client):
    with patch('routes.claim_results.db') as mock_db:
        mock_db.session.get.return_value = None
        res = client.get('/api/claim/fake/diversity')
        assert res.status_code == 200
        data = res.get_json()
        assert data['is_single_source_biased'] == False