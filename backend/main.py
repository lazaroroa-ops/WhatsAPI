from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from marshmallow import Schema, fields, validate, ValidationError
from http import HTTPStatus
from flasgger import Swagger

import os
import ssl
import uuid
import hashlib
import logging

from models import db, User, Mail
from resources import MailResource, MailDetailResource, ChangePassResource, DeleteAccountResource, AdminStatsResource

app = Flask(__name__)


CORS(
	app,
	resources={
		r"/*": {
			"origins": ["https://www.dominio-frontend.com"],
			"methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
			"allow_headers": ["Content-Type", "Authorization", "X-API-KEY"]
		}
	}
)

base_dir = os.path.abspath(os.path.dirname(__file__))
cert_path = os.path.join(base_dir, 'server.crt')
key_path = os.path.join(base_dir, 'server.key')


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jwtdatabase.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'jwtdatabase.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret'  # Cambia esto por una clave secreta segura en producción
app.config['SWAGGER'] = {"title": "WhatsAPI, a mail API"}

db.init_app(app)
jwt = JWTManager(app)
api = Api(app)

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec_1",
            "route": "/apispec_1.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/",
    "securityDefinitions": {
        "bearerAuth": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Bearer token. Example: \"Bearer {token}\""
        },
        "apiKeyAuth": {
            "type": "apiKey",
            "name": "X-API-KEY",
            "in": "header",
            "description": "API Key for secondary validation."
        }
    },
    "uiversion": 3
}

swagger = Swagger(app, config=swagger_config)


logging.basicConfig(
	filename='audit.log',
	level=logging.INFO,
	format='%(asctime)s %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

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
		"""
		file: swagger/register_post.yaml
		"""
		if request.content_type != 'application/json':
			return {"error": "Content must be in JSON format"}, HTTPStatus.UNSUPPORTED_MEDIA_TYPE
		
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

		logger.info(f"New user registered: {username}")
		return {'message': 'User registered successfully.'}, HTTPStatus.CREATED


class Login(Resource):
	def post(self):
		"""
		file: swagger/login_post.yaml
		"""
		if request.content_type != 'application/json':
			return {"error": "Content must be in JSON format"}, HTTPStatus.UNSUPPORTED_MEDIA_TYPE

		data = request.get_json()
		username = data.get('username')
		password = data.get('password')
		
		if not username or not password:
			logger.warning(f"Failed login attempt, no username or password")
			return {'error': 'Username and password are required.'}, HTTPStatus.BAD_REQUEST
		
		user = User.query.filter_by(username=username).first()
		if not user or not check_password_hash(user.password, password):
			if not user:
				logger.warning(f"Failed login attempt, username does not exist")
			else:
				logger.warning(f"Failed login attempt for: {user.username}")
			return {'error': 'Invalid username or password.'}, HTTPStatus.UNAUTHORIZED
		
		return {'access_token': create_access_token(identity=username), 'api_key': user.api_key}, HTTPStatus.OK


api.add_resource(Register, '/register')
api.add_resource(Login, '/login')
api.add_resource(MailResource, '/mail')
api.add_resource(MailDetailResource, '/mail/<int:mail_id>')
api.add_resource(ChangePassResource, '/change-pass')
api.add_resource(DeleteAccountResource, '/del-account')
api.add_resource(AdminStatsResource, '/admin/stats')



@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

	#PARA QUE FUNCIONE CON LA API
    if request.path.startswith('/apidocs') or request.path.startswith('/flasgger_static'):
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:;"
        )
    else:
        response.headers['Content-Security-Policy'] = "default-src 'self'"

    return response


@app.errorhandler(404)
def not_found(error):
	return {"error": "Resource not found."}, 404

@app.errorhandler(Exception)
def handle_exception(e):
	logger.error(f"Internal error: {e}")
	return {"error": "Something went wrong."}, 500


if __name__ == '__main__':
	with app.app_context():
		db.create_all()

	ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
	ssl_context.load_cert_chain(certfile=cert_path, keyfile=key_path, password='password1')

	app.run(ssl_context=ssl_context, debug=True)
