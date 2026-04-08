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


def test_get_users_unauthorized(client):
    res = client.get('/api/admin/users')
    assert res.status_code == 403


def test_get_users_returns_list(client):
    with patch('routes.admin.User') as mock_user:
        mock_query = MagicMock()
        mock_user.query.with_entities.return_value.all.return_value = [
            MagicMock(id="1", username="alice", email="alice@test.com", membership_status="free")
        ]

        with client.session_transaction() as sess:
            sess['is_admin'] = True

        res = client.get('/api/admin/users')
        assert res.status_code == 200
        data = res.get_json()

        assert len(data) == 1
        assert data[0]['username'] == 'alice'


def test_get_users_empty_database(client):
    with patch('routes.admin.User') as mock_user:
        mock_user.query.with_entities.return_value.all.return_value = []

        with client.session_transaction() as sess:
            sess['is_admin'] = True

        res = client.get('/api/admin/users')
        assert res.status_code == 200
        assert res.get_json() == []


def test_get_users_database_failure(client):
    with patch('routes.admin.User') as mock_user:
        mock_user.query.with_entities.side_effect = Exception("DB error")

        with client.session_transaction() as sess:
            sess['is_admin'] = True

        res = client.get('/api/admin/users')
        assert res.status_code == 500