#only needs to be run once to create the database and tables


from app import app, db
from models import *

with app.app_context():
    db.create_all()  # creates all tables that don't already exist