import pytest
from admin import Admin

class TestAdminCreation:
	def test_valid_admin_creation(self):
		admin = Admin("admin1", "admin@example.com", "John", "Admin")
		assert admin.username == "admin1"
		assert admin.email_address == "admin@example.com"
		assert admin.membership_status == "Admin"
		assert admin.is_admin == True
	
	def test_admin_has_unlimited_tokens(self):
		admin = Admin("admin1", "admin@example.com", "John", "Admin")
		assert admin.has_unlimited_tokens == True
		assert admin.daily_text_tokens_remaining == -1
		assert admin.daily_file_tokens_remaining == -1

class TestUserManagement:
	def test_ban_user_success(self):
		admin = Admin("admin1", "admin@example.com", "John", "Admin")
		result = admin.ban_user("user123")
		assert result["action"] == "ban"
		assert result["user_id"] == "user123"
		assert result["status"] == "success"
	
	def test_ban_user_empty_id_raises_error(self):
		admin = Admin("admin1", "admin@example.com", "John", "Admin")
		with pytest.raises(ValueError):
			admin.ban_user("")
	
	def test_suspend_user_success(self):
		admin = Admin("admin1", "admin@example.com", "John", "Admin")
		result = admin.suspend_user("user123", 14)
		assert result["action"] == "suspend"
		assert result["duration_days"] == 14
		assert result["status"] == "success"
	
	def test_suspend_user_invalid_duration(self):
		admin = Admin("admin1", "admin@example.com", "John", "Admin")
		with pytest.raises(ValueError):
			admin.suspend_user("user123", -5)
	
	def test_delete_user_success(self):
		admin = Admin("admin1", "admin@example.com", "John", "Admin")
		result = admin.delete_user("user123")
		assert result["action"] == "delete"
		assert result["status"] == "success"
	
	def test_create_user_success(self):
		admin = Admin("admin1", "admin@example.com", "John", "Admin")
		result = admin.create_user("newuser", "new@example.com", "Jane", "Doe")
		assert result["action"] == "create"
		assert result["username"] == "newuser"
		assert result["status"] == "success"
	
	def test_create_user_empty_username_raises_error(self):
		admin = Admin("admin1", "admin@example.com", "John", "Admin")
		with pytest.raises(ValueError):
			admin.create_user("", "new@example.com", "Jane", "Doe")

class TestServiceManagement:
	def test_stop_service(self):
		admin = Admin("admin1", "admin@example.com", "John", "Admin")
		result = admin.stop_service()
		assert result["action"] == "stop_service"
		assert result["status"] == "success"
		assert admin.is_service_running() == False
	
	def test_start_service(self):
		admin = Admin("admin1", "admin@example.com", "John", "Admin")
		admin.stop_service()
		result = admin.start_service()
		assert result["action"] == "start_service"
		assert result["status"] == "success"
		assert admin.is_service_running() == True
	
	def test_get_all_users(self):
		admin = Admin("admin1", "admin@example.com", "John", "Admin")
		users = admin.get_all_users()
		assert isinstance(users, list)

class TestTokenOverride:
	def test_admin_tokens_cannot_be_modified(self):
		admin = Admin("admin1", "admin@example.com", "John", "Admin")
		admin.daily_text_tokens_remaining = 100
		admin.daily_file_tokens_remaining = 50
		# Tokens should remain unlimited (-1)
		assert admin.daily_text_tokens_remaining == -1
		assert admin.daily_file_tokens_remaining == -1