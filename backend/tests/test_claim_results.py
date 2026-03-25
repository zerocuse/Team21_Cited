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

def test_missing_claim_returns_404(client):
    with patch('routes.claim_results.CredibilityCalculator') as mock:
        mock.return_value.calculate.side_effect = Exception("not found")
        res = client.get('/api/claim/fake123/result')
        assert res.status_code == 404

def test_high_credibility_label(client):
    with patch('routes.claim_results.CredibilityCalculator') as cc, \
         patch('routes.claim_results.SourceReputation') as sr, \
         patch('routes.claim_results.FactComparisonEngine') as fc:
        cc.return_value.calculate.return_value = 80
        sr.return_value.get_score.return_value = 90
        fc.return_value.detect_contradiction.return_value = False
        res = client.get('/api/claim/abc123/result')
        data = res.get_json()
        assert data['credibility_label'] == 'High'

def test_contradiction_detected(client):
    with patch('routes.claim_results.CredibilityCalculator') as cc, \
         patch('routes.claim_results.SourceReputation') as sr, \
         patch('routes.claim_results.FactComparisonEngine') as fc:
        cc.return_value.calculate.return_value = 40
        sr.return_value.get_score.return_value = 50
        fc.return_value.detect_contradiction.return_value = True
        res = client.get('/api/claim/abc123/result')
        data = res.get_json()
        assert data['contradiction_detected'] == True