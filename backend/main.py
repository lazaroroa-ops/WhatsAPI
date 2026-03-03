from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash

from marshmallow import Schema, fields, validate, ValidationError
from http import HTTPStatus

import os
import ssl

from models import db, User, Message

app = Flask(__name__)
#api = Api(app)

base_dir = os.path.abspath(os.path.dirname(__file__))
cert_path = os.path.join(base_dir, 'server.crt')
key_path = os.path.join(base_dir, 'server.key')


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jwtdatabase.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'jwtdatabase.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret'  # Cambia esto por una clave secreta segura en producción

db.init_app(app)
jwt = JWTManager(app)
api = Api(app)

# Se ha pasado a modelo el user
### USER REGISTER VALIDATION ###

def validate_complexity(password):
    if not any(char.isupper() for char in password):
        raise ValidationError("Password must contain at least one uppercase letter.")
    if not any(char.isdigit() for char in password):
        raise ValidationError("Password must contain at least one digit.")

class UserSchema(Schema):
	username = fields.Email(required=True)
	password = fields.Str(
		required=True,
		validate=[
			validate.Length(min=8, max=60, error=f"Password must be between 8 and 60 characters long."),
			validate_complexity
		]	
	)

user_schema = UserSchema()


class Register(Resource):
	def post(self):
		data = request.get_json()
		username = data.get('username')
		password = data.get('password')
		
		try:
			user_schema.load(data)
		except ValidationError as e:
			return {'error': e.messages}, HTTPStatus.BAD_REQUEST
		
		if User.query.filter_by(username=username).first():
			return {'error': {'username': 'Username already exists.'}}, HTTPStatus.BAD_REQUEST

		role = 'admin' if User.query.count() == 0 else 'user'
		
		hashed_password = generate_password_hash(password)
		new_user = User(username=username, password=hashed_password, role=role)
		db.session.add(new_user)
		db.session.commit()
		
		return {'message': 'User registered successfully.'}, HTTPStatus.CREATED


class Login(Resource):
	def post(self):
		data = request.get_json()
		username = data.get('username')
		password = data.get('password')
		
		if not username or not password:
			return {'error': 'Username and password are required.'}, HTTPStatus.BAD_REQUEST
		
		user = User.query.filter_by(username=username).first()
		if not user or not check_password_hash(user.password, password):
			return {'error': 'Invalid username or password.'}, HTTPStatus.UNAUTHORIZED
		
		return {'access_token': create_access_token(identity=username)}, HTTPStatus.OK


class ProtectedResource(Resource):
	@jwt_required()
	def get(self):
		current_user = get_jwt_identity()
		return {'message': f'Hello, {current_user}'}, 200

api.add_resource(Register, '/register')
api.add_resource(Login, '/login')

api.add_resource(ProtectedResource, '/protected')


if __name__ == '__main__':
	with app.app_context():
		db.create_all()

	ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
	ssl_context.load_cert_chain(certfile=cert_path, keyfile=key_path, password='password1')

	app.run(ssl_context=ssl_context, debug=True)
