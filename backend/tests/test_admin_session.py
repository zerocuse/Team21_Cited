import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from routes.auth import auth_bp
from flask import Flask, session

@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(auth_bp)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test'
    return app.test_client()

def test_admin_login_sets_session(client):
    with client.session_transaction() as sess:
        sess['is_admin'] = True
    with client.session_transaction() as sess:
        assert sess.get('is_admin') == True

def test_non_admin_does_not_set_session(client):
    with client.session_transaction() as sess:
        sess.pop('is_admin', None)
    with client.session_transaction() as sess:
        assert sess.get('is_admin') is None

def test_logout_clears_session(client):
    with client.session_transaction() as sess:
        sess['is_admin'] = True
    with client.session_transaction() as sess:
        sess.pop('is_admin', None)
    with client.session_transaction() as sess:
        assert sess.get('is_admin') is None