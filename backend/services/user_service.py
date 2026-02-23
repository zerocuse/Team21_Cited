from models import User, db
import re

#Will put a new user into the database
def create_user(username: str, email_address: str, membership_status: str, first_name: str, last_name: str, password_hash: str) -> User:

    # Validation
    email_pattern = r'^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'

    if not username or not username.strip():
        raise ValueError("Username cannot be null or empty")
    if not email_address or not re.match(email_pattern, email_address):
        raise ValueError("Invalid email address")
    if not first_name or not first_name.strip():
        raise ValueError("First name cannot be null or empty")
    if not last_name or not last_name.strip():
        raise ValueError("Last name cannot be null or empty")
    
    # create a user instance
    new_user = User(
        #userID is created automatically
        username=username,
        email_address=email_address,
        password_hash=password_hash,
        membership_status=membership_status,
        #creation_date is created automatically
        first_name=first_name,
        last_name=last_name)
    
    db.session.add(new_user)
    db.session.commit()
    return new_user
    