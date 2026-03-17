from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from models.models import User, db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

TOKEN_SALT = 'auth-token'
TOKEN_MAX_AGE = 60 * 60 * 24 * 30  # 30 days


def _make_token(user_id):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(user_id, salt=TOKEN_SALT)


def _decode_token(token):
    """Returns user_id int or None if invalid/expired."""
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        return s.loads(token, salt=TOKEN_SALT, max_age=TOKEN_MAX_AGE)
    except (SignatureExpired, BadSignature):
        return None


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

    token = _make_token(new_user.userID)
    return jsonify({'token': token, 'user': new_user.to_dict()}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    user = db.session.query(User).filter_by(email=data.get('email_address')).first()
    if not user or not check_password_hash(user.password_hash, data.get('password', '')):
        return jsonify({'error': 'Invalid email or password'}), 401

    token = _make_token(user.userID)
    return jsonify({'token': token, 'user': user.to_dict()}), 200


@auth_bp.route('/me', methods=['GET'])
def me():
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.removeprefix('Bearer ').strip()

    if not token:
        return jsonify({'error': 'Missing token'}), 401

    user_id = _decode_token(token)
    if user_id is None:
        return jsonify({'error': 'Invalid or expired token'}), 401

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify(user.to_dict()), 200
