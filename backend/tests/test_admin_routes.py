import pytest
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
    return app.test_client()

def test_get_users_unauthorized(client):
    res = client.get('/api/admin/users')
    assert res.status_code == 403

def test_ban_user_unauthorized(client):
    res = client.post('/api/admin/ban/user123')
    assert res.status_code == 403

def test_delete_user_unauthorized(client):
    res = client.delete('/api/admin/delete/user123')
    assert res.status_code == 403

def test_create_user_missing_fields(client):
    with client.session_transaction() as sess:
        sess['is_admin'] = True
    res = client.post('/api/admin/create',
        json={'username': '', 'email': '', 'first_name': '', 'last_name': ''},
        content_type='application/json')
    assert res.status_code == 400