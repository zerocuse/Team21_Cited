import re
from typing import List

class User:
	def __init__(self, username: str, email_address: str, membership_status: str, first_name: str, last_name: str, daily_text_tokens_remaining: int, daily_file_tokens_remaining: int): """
		Initialize User with all required fields and validation.
	
		Args:
			username: User's username
			email_address: User's email address
			membership_status: Membership level (Free/Pro/Enterprise)
			first_name: User's first name
			last_name: User's last name
			daily_text_tokens_remaining: Remaining text input tokens
			daily_file_tokens_remaining: Remaining file input tokens
		"""
		# Email validation pattern
		email_pattern = r'^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
	
		# Validation
		if not username or not username.strip():
			raise ValueError("Username cannot be null or empty")
		if not email_address or not re.match(email_pattern, email_address):
			raise ValueError("Invalid email address")
		if not first_name or not first_name.strip():
			raise ValueError("First name cannot be null or empty")
		if not last_name or not last_name.strip():
			raise ValueError("Last name cannot be null or empty")
		if daily_text_tokens_remaining < 0:
			raise ValueError("Text tokens cannot be negative")
		if daily_file_tokens_remaining < 0:
			raise ValueError("File tokens cannot be negative")
	
		# Initialize fields
		self._username = username
		self._email_address = email_address
		self._membership_status = membership_status
		self._first_name = first_name
		self._last_name = last_name
		self._previous_queries: List[str] = []
		self._daily_text_tokens_remaining = daily_text_tokens_remaining
		self._daily_file_tokens_remaining = daily_file_tokens_remaining
	
	# Getters
	@property
	def username(self) -> str:
		return self._username
	
	@property
	def email_address(self) -> str:
		return self._email_address
	
	@property
	def membership_status(self) -> str:
		return self._membership_status
	
	@property
	def first_name(self) -> str:
		return self._first_name
	
	@property
	def last_name(self) -> str:
		return self._last_name
	
	@property
	def previous_queries(self) -> List[str]:
		return self._previous_queries.copy()
	
	@property
	def daily_text_tokens_remaining(self) -> int:
		return self._daily_text_tokens_remaining
	
	@property
	def daily_file_tokens_remaining(self) -> int:
		return self._daily_file_tokens_remaining
	
	# Setters
	@username.setter
	def username(self, value: str):
		if not value or not value.strip():
			raise ValueError("Username cannot be null or empty")
		self._username = value
	
	@email_address.setter
	def email_address(self, value: str):
		email_pattern = r'^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
		if not value or not re.match(email_pattern, value):
			raise ValueError("Invalid email address")
		self._email_address = value
	
	@membership_status.setter
	def membership_status(self, value: str):
		self._membership_status = value
	
	@first_name.setter
	def first_name(self, value: str):
		if not value or not value.strip():
			raise ValueError("First name cannot be null or empty")
		self._first_name = value
	
	@last_name.setter
	def last_name(self, value: str):
		if not value or not value.strip():
			raise ValueError("Last name cannot be null or empty")
		self._last_name = value
	
	@daily_text_tokens_remaining.setter
	def daily_text_tokens_remaining(self, value: int):
		if value < 0:
			raise ValueError("Text tokens cannot be negative")
		self._daily_text_tokens_remaining = value
	
	@daily_file_tokens_remaining.setter
	def daily_file_tokens_remaining(self, value: int):
		if value < 0:
			raise ValueError("File tokens cannot be negative")
		self._daily_file_tokens_remaining = value
	
	# Helper methods
	def add_query(self, query: str):
		"""Add a query to the user's query history."""
		if query and query.strip():
			self._previous_queries.append(query)