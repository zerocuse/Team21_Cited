from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from models.models import User, db  # import db from your models

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    required = ['email_address', 'password', 'first_name', 'last_name', 'username']
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields'}), 400

    if db.session.query(User).filter_by(email=data['email_address']).first():
        return jsonify({'error': 'Email already registered'}), 409

    if db.session.query(User).filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already taken'}), 409

    new_user = User(
        email=data['email_address'],
        password_hash=generate_password_hash(data['password']),
        first_name=data['first_name'],
        last_name=data['last_name'],
        username=data['username'],
    )
    db.session.add(new_user)
    db.session.commit()

    token = secrets.token_hex(32)  # swap for JWT later if needed

    return jsonify({
        'token': token,
        'user': {
            'first_name': new_user.first_name,
            'last_name': new_user.last_name,
            'username': new_user.username,
            'membership_status': new_user.membership_status,
        }
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    user = db.session.query(User).filter_by(email=data.get('email_address')).first()
    if not user or not check_password_hash(user.password_hash, data.get('password', '')):
        return jsonify({'error': 'Invalid email or password'}), 401

    token = secrets.token_hex(32)

    return jsonify({
        'token': token,
        'user': {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'is_member': user.is_member.value,
        }
    }), 200