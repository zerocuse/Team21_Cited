##This is where the SQLalchemy database models and configurations are going to go

#Adam is going to implement this in sprint 3

from extensions import db
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

class User(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50))
    last_name  = db.Column(db.String(50))
    username   = db.Column(db.String(50), unique=True)
    is_member  = db.Column(db.Boolean, default=False)

    def set_password(self, raw):
        self.password = bcrypt.generate_password_hash(raw).decode('utf-8')

    def check_password(self, raw):
        return bcrypt.check_password_hash(self.password, raw)

    def to_dict(self):
        return {
            'id':         self.id,
            'email':      self.email,
            'first_name': self.first_name,
            'last_name':  self.last_name,
            'username':   self.username,
            'is_member':  self.is_member,
        }