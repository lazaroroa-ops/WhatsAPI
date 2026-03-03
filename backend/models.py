# TODO: Pasar los modelos de main a modelos separados:

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy() # Procesado de DB igual, pero lo separo por app

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='user')
    #api_key = db.Column(db.String(64), unique=True, nullable=True)

    def __repr__(self):
        return f'<User {self.username}>'
