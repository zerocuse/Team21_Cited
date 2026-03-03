from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt
from user_services import create_user, get_user_by_email, get_user_by_id  # your existing functions

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
bcrypt = Bcrypt()


@auth_bp.post('/register')
def register():
    data = request.get_json()

    # Check if email is already taken
    try:
        get_user_by_email(data['email_address'])
        return jsonify({'error': 'Email already in use'}), 409
    except ValueError:
        pass  # good — user doesn't exist yet

    try:
        password_hash = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        user = create_user(
            username          = data['username'],
            email_address     = data['email_address'],
            membership_status = data.get('membership_status', 'free'),
            first_name        = data['first_name'],
            last_name         = data['last_name'],
            password_hash     = password_hash,
            profile_picture   = data.get('profile_picture', None),
        )
        token = create_access_token(identity=str(user.userID))
        return jsonify({'token': token, 'user': user.to_dict()}), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@auth_bp.post('/login')
def login():
    data = request.get_json()

    try:
        user = get_user_by_email(data['email_address'])
    except ValueError:
        return jsonify({'error': 'Invalid credentials'}), 401

    if not bcrypt.check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401

    token = create_access_token(identity=str(user.userID))
    return jsonify({'token': token, 'user': user.to_dict()}), 200


@auth_bp.get('/me')
@jwt_required()
def me():
    try:
        user = get_user_by_id(int(get_jwt_identity()))
        return jsonify(user.to_dict())
    except ValueError as e:
        return jsonify({'error': str(e)}), 404