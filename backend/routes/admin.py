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