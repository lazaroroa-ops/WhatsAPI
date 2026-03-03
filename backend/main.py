from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash

from marshmallow import Schema, fields, validate, ValidationError
from http import HTTPStatus

import os
import ssl
import uuid
import hashlib
import logging

from models import db, User, Mail
from resources import MailResource, MailDetailResource, ChangePassResource, DeleteAccountResource

app = Flask(__name__)


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
logging.basicConfig(
    filename='audit.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

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
		api_key = hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()
		
		hashed_password = generate_password_hash(password)
		new_user = User(username=username, password=hashed_password, role=role, api_key=api_key)
		db.session.add(new_user)
		db.session.commit()

		logging.info(f"New user registered: {username}")
		return {'message': 'User registered successfully.'}, HTTPStatus.CREATED


class Login(Resource):
	def post(self):
		data = request.get_json()
		username = data.get('username')
		password = data.get('password')
		
		if not username or not password:
			logging.warning(f"Failed login attempt, no username or password")
			return {'error': 'Username and password are required.'}, HTTPStatus.BAD_REQUEST
		
		user = User.query.filter_by(username=username).first()
		if not user or not check_password_hash(user.password, password):
			logging.warning(f"Failed login attempt for: {user.username}")
			return {'error': 'Invalid username or password.'}, HTTPStatus.UNAUTHORIZED
		
		return {'access_token': create_access_token(identity=username), 'api_key': user.api_key}, HTTPStatus.OK


api.add_resource(Register, '/register')
api.add_resource(Login, '/login')
api.add_resource(MailResource, '/mail')
api.add_resource(MailDetailResource, '/mail/<int:mail_id>')
api.add_resource(ChangePassResource, '/change-pass')
api.add_resource(DeleteAccountResource, '/del-account')

@app.after_request
def add_security_headers(response):
    #CORS
    origin = request.headers.get('Origin')
    if origin in ['https://localhost:5000', 'http://localhost:5000']:
        response.headers['Access-Control-Allow-Origin'] = origin
    
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,X-API-KEY'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
    
    #Headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response


if __name__ == '__main__':
	with app.app_context():
		db.create_all()

	ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
	ssl_context.load_cert_chain(certfile=cert_path, keyfile=key_path, password='password1')

	app.run(ssl_context=ssl_context, debug=True)
