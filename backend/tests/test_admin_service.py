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

def test_service_status_unauthorized(client):
    res = client.get('/api/admin/service/status')
    assert res.status_code == 403

def test_stop_service_unauthorized(client):
    res = client.post('/api/admin/service/stop')
    assert res.status_code == 403

def test_start_service_unauthorized(client):
    res = client.post('/api/admin/service/start')
    assert res.status_code == 403

def test_service_status_authorized(client):
    with client.session_transaction() as sess:
        sess['is_admin'] = True
    res = client.get('/api/admin/service/status')
    assert res.status_code == 200
    data = res.get_json()
    assert 'running' in data

def test_stop_then_start_service(client):
    with client.session_transaction() as sess:
        sess['is_admin'] = True
    stop = client.post('/api/admin/service/stop')
    assert stop.get_json()['status'] == 'success'
    start = client.post('/api/admin/service/start')
    assert start.get_json()['status'] == 'success'