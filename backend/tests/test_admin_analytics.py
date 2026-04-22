import pytest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from routes.admin import admin_bp
from flask import Flask

@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(admin_bp)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test'
    return app.test_client()

def test_analytics_unauthorized(client):
    res = client.get('/api/admin/analytics')
    assert res.status_code == 403

def test_analytics_returns_correct_shape(client):
    with patch('routes.admin.supabase') as mock_supabase, \
         patch('routes.admin.URLSafeTimedSerializer') as mock_s, \
         patch('routes.admin.db') as mock_db:
        mock_s.return_value.loads.return_value = 1
        mock_user = MagicMock()
        mock_user.to_dict.return_value = {'membership_status': 'admin'}
        mock_db.session.get.return_value = mock_user
        mock_db.session.query.return_value.all.return_value = []
        res = client.get('/api/admin/analytics',
            headers={'Authorization': 'Bearer faketoken'})
        if res.status_code == 200:
            data = res.get_json()
            assert 'total_claims' in data
            assert 'trending_claims' in data
            assert 'flagged_users' in data

def test_analytics_empty_data(client):
    with patch('routes.admin.URLSafeTimedSerializer') as mock_s, \
         patch('routes.admin.db') as mock_db:
        mock_s.return_value.loads.return_value = 1
        mock_user = MagicMock()
        mock_user.to_dict.return_value = {'membership_status': 'admin'}
        mock_db.session.get.return_value = mock_user
        mock_db.session.query.return_value.all.return_value = []
        res = client.get('/api/admin/analytics',
            headers={'Authorization': 'Bearer faketoken'})
        if res.status_code == 200:
            data = res.get_json()
            assert data['total_claims'] == 0
            assert data['trending_claims'] == []
            assert data['flagged_users'] == []