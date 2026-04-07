import pytest
from unittest.mock import patch
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

def test_high_label(client):
    with patch('routes.claim_results.CredibilityCalculator') as cc:
        cc.return_value.calculate.return_value = 80
        res = client.get('/api/claim/abc/credibility')
        data = res.get_json()
        assert data['credibility_label'] == 'High'

def test_medium_label(client):
    with patch('routes.claim_results.CredibilityCalculator') as cc:
        cc.return_value.calculate.return_value = 55
        res = client.get('/api/claim/abc/credibility')
        data = res.get_json()
        assert data['credibility_label'] == 'Medium'

def test_low_label(client):
    with patch('routes.claim_results.CredibilityCalculator') as cc:
        cc.return_value.calculate.return_value = 20
        res = client.get('/api/claim/abc/credibility')
        data = res.get_json()
        assert data['credibility_label'] == 'Low'

def test_missing_claim_returns_not_available(client):
    with patch('routes.claim_results.CredibilityCalculator') as cc:
        cc.return_value.calculate.side_effect = Exception("not found")
        res = client.get('/api/claim/fake/credibility')
        data = res.get_json()
        assert data['credibility_label'] == 'Not Available'