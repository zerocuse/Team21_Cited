from flask import Blueprint, jsonify, request, session
from models.admin import Admin

admin_bp = Blueprint('admin', __name__)

def get_admin():
    return Admin(
        username="admin",
        email_address="admin@cited.com",
        first_name="Admin",
        last_name="User"
    )

@admin_bp.route('/api/admin/users', methods=['GET'])
def get_all_users():
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 403
    admin = get_admin()
    users = admin.get_all_users()
    return jsonify(users), 200

@admin_bp.route('/api/admin/ban/<user_id>', methods=['POST'])
def ban_user(user_id):
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 403
    admin = get_admin()
    result = admin.ban_user(user_id)
    return jsonify(result), 200

@admin_bp.route('/api/admin/suspend/<user_id>', methods=['POST'])
def suspend_user(user_id):
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 403
    data = request.get_json()
    days = data.get('duration_days', 7)
    admin = get_admin()
    result = admin.suspend_user(user_id, duration_days=int(days))
    return jsonify(result), 200

@admin_bp.route('/api/admin/delete/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 403
    admin = get_admin()
    result = admin.delete_user(user_id)
    return jsonify(result), 200

@admin_bp.route('/api/admin/create', methods=['POST'])
def create_user():
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 403
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    membership = data.get('membership_status', 'Free')

    if not username or not email or not first_name or not last_name:
        return jsonify({"error": "All fields are required"}), 400

    admin = get_admin()
    result = admin.create_user(username, email, first_name, last_name, membership)
    return jsonify(result), 200

_admin_instance = get_admin()

@admin_bp.route('/api/admin/service/status', methods=['GET'])
def service_status():
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 403
    return jsonify({"running": _admin_instance.is_service_running()}), 200

@admin_bp.route('/api/admin/service/stop', methods=['POST'])
def stop_service():
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 403
    result = _admin_instance.stop_service()
    return jsonify(result), 200

@admin_bp.route('/api/admin/service/start', methods=['POST'])
def start_service():
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 403
    result = _admin_instance.start_service()
    return jsonify(result), 200