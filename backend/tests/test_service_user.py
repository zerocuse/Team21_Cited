from app import app, db
from models import User
from services.user_service import create_user

create_user("adamknell", "ajknell@syr.edu", "admin", "Adam", "Knell", "password") 

