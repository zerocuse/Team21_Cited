from typing import List, Dict, Optional
from user import User

class Admin(User):
	"""
	Admin class with elevated privileges.
	
	Admins have:
	- Unlimited tokens (tokens never decrease)
	- User management capabilities (ban, suspend, delete, create)
	- Service management (stop/start service)
	- Access to view all users
	"""
	
	def __init__(self, username: str, email_address: str, 
				 first_name: str, last_name: str):
		"""
		Initialize Admin user.
		
		Args:
			username: Admin username
			email_address: Admin email
			first_name: Admin first name
			last_name: Admin last name
		"""
		# Initialize with unlimited tokens (represented as -1)
		super().__init__(
			username=username,
			email_address=email_address,
			membership_status="Admin",
			first_name=first_name,
			last_name=last_name,
			daily_text_tokens_remaining=-1,  # Unlimited
			daily_file_tokens_remaining=-1   # Unlimited
		)
		self._is_admin = True
		self._service_running = True
	
	@property
	def is_admin(self) -> bool:
		"""Check if user has admin privileges."""
		return self._is_admin
	
	@property
	def has_unlimited_tokens(self) -> bool:
		"""Admin always has unlimited tokens."""
		return True
	
	def ban_user(self, user_id: str) -> Dict[str, str]:
		"""
		Ban a user from the system.
		
		Args:
			user_id: ID of user to ban
			
		Returns:
			Dictionary with operation result
			
		Raises:
			ValueError: If user_id is invalid
		"""
		if not user_id or not user_id.strip():
			raise ValueError("User ID cannot be empty")
		
		# In future: integrate with database
		return {
			"action": "ban",
			"user_id": user_id,
			"status": "success",
			"message": f"User {user_id} has been banned"
		}
	
	def suspend_user(self, user_id: str, duration_days: int = 7) -> Dict[str, str]:
		"""
		Suspend a user temporarily.
		
		Args:
			user_id: ID of user to suspend
			duration_days: Number of days to suspend (default 7)
			
		Returns:
			Dictionary with operation result
			
		Raises:
			ValueError: If parameters are invalid
		"""
		if not user_id or not user_id.strip():
			raise ValueError("User ID cannot be empty")
		if duration_days <= 0:
			raise ValueError("Suspension duration must be positive")
		
		return {
			"action": "suspend",
			"user_id": user_id,
			"duration_days": duration_days,
			"status": "success",
			"message": f"User {user_id} suspended for {duration_days} days"
		}
	
	def delete_user(self, user_id: str) -> Dict[str, str]:
		"""
		Delete a user from the system.
		
		Args:
			user_id: ID of user to delete
			
		Returns:
			Dictionary with operation result
			
		Raises:
			ValueError: If user_id is invalid
		"""
		if not user_id or not user_id.strip():
			raise ValueError("User ID cannot be empty")
		
		return {
			"action": "delete",
			"user_id": user_id,
			"status": "success",
			"message": f"User {user_id} has been deleted"
		}
	
	def create_user(self, username: str, email: str, 
				   first_name: str, last_name: str,
				   membership_status: str = "Free") -> Dict[str, str]:
		"""
		Create a new user.
		
		Args:
			username: New user's username
			email: New user's email
			first_name: New user's first name
			last_name: New user's last name
			membership_status: Membership level (default "Free")
			
		Returns:
			Dictionary with operation result
			
		Raises:
			ValueError: If parameters are invalid
		"""
		if not username or not username.strip():
			raise ValueError("Username cannot be empty")
		if not email or not email.strip():
			raise ValueError("Email cannot be empty")
		if not first_name or not first_name.strip():
			raise ValueError("First name cannot be empty")
		if not last_name or not last_name.strip():
			raise ValueError("Last name cannot be empty")
		
		return {
			"action": "create",
			"username": username,
			"email": email,
			"status": "success",
			"message": f"User {username} created successfully"
		}
	
	def get_all_users(self) -> List[Dict[str, str]]:
		"""
		Get list of all users in the system.
		
		Returns:
			List of user dictionaries
			
		Note:
			This is a placeholder. In future, will query database.
		"""
		# Placeholder implementation
		return []
	
	def stop_service(self) -> Dict[str, str]:
		"""
		Stop the service.
		
		Returns:
			Dictionary with operation result
		"""
		self._service_running = False
		return {
			"action": "stop_service",
			"status": "success",
			"message": "Service stopped successfully"
		}
	
	def start_service(self) -> Dict[str, str]:
		"""
		Start the service.
		
		Returns:
			Dictionary with operation result
		"""
		self._service_running = True
		return {
			"action": "start_service",
			"status": "success",
			"message": "Service started successfully"
		}
	
	def is_service_running(self) -> bool:
		"""Check if service is currently running."""
		return self._service_running
	
	# Override token setters to prevent modification
	@User.daily_text_tokens_remaining.setter
	def daily_text_tokens_remaining(self, value: int):
		"""Admin tokens cannot be modified (always unlimited)."""
		pass  # Ignore attempts to set tokens
	
	@User.daily_file_tokens_remaining.setter
	def daily_file_tokens_remaining(self, value: int):
		"""Admin tokens cannot be modified (always unlimited)."""
		pass  # Ignore attempts to set tokens