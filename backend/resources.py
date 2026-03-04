from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Mail
from http import HTTPStatus
from flasgger import swag_from

from marshmallow import Schema, fields, validate, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash

def validate_complexity(password):
	if not any(char.isupper() for char in password):
		raise ValidationError("Password must contain at least one uppercase letter.")
	if not any(char.isdigit() for char in password):
		raise ValidationError("Password must contain at least one digit.")

class PasswordSchema(Schema):
	password = fields.Str(
		required=True,
		validate=[
			validate.Length(min=8, max=60, error=f"Password must be between 8 and 60 characters long."),
			validate_complexity
		]	
	)

password_schema = PasswordSchema()

def validate_api_key():
	api_key = request.headers.get('X-API-KEY')
	if not api_key:
		return False, {"message": "API Key is missing"}, 401
	user = User.query.filter_by(api_key=api_key).first()
	if not user:
		return False, {"message": "Invalid API Key"}, 401

	current_user_username = get_jwt_identity()
	if user.username != current_user_username:
		return False, {"message": "JWT and API Key mismatch"}, 403
	return True, user, 200
	

class ChangePassResource(Resource):
	@jwt_required()
	@swag_from('swagger/change_pass_put.yaml')
	def put(self):
		valid, auth_user_or_err, code = validate_api_key()
		if not valid:
			return auth_user_or_err, code
		
		username = get_jwt_identity()
		user = User.query.filter_by(username=username).first()
		
		if request.content_type != 'application/json':
			return {"error": "Content must be in JSON format"}, HTTPStatus.UNSUPPORTED_MEDIA_TYPE

		data = request.get_json()
		old_password = data.get('old_password')
		new_password = data.get('new_password')

		if not old_password or not new_password:
			return {"message": "Old and new passwords are required"}, 400

		if not check_password_hash(user.password, old_password):
			return {"message": "Old password is not correct"}, 401

		try:
			password_schema.load(dict(password=new_password))
		except ValidationError as e:
			return {'message': e.messages}, 400
			
		user.password = generate_password_hash(new_password)
		db.session.commit()
		
		return {"message": "Password updated successfully"}, 200


class DeleteAccountResource(Resource):
	@jwt_required()
	@swag_from('swagger/del_account_delete.yaml')
	def delete(self):
		valid, auth_user_or_err, code = validate_api_key()
		if not valid:
			return auth_user_or_err, code
		
		username = get_jwt_identity()
		user = User.query.filter_by(username=username).first()

		if request.content_type != 'application/json':
			return {"error": "Content must be in JSON format"}, HTTPStatus.UNSUPPORTED_MEDIA_TYPE

		data = request.get_json()
		password = data.get('password')

		if not password:
			return {"message": "Password is required"}, 400

		if not check_password_hash(user.password, password):
			return {"message": "Password does not match"}, 401
			
		db.session.delete(user)
		db.session.commit()
		
		return {"message": "Account deleted successfully"}, 200


class MailResource(Resource):
	@jwt_required()
	@swag_from('swagger/mail_post.yaml')
	def post(self):
		valid, auth_user_or_err, code = validate_api_key()
		if not valid:
			return auth_user_or_err, code

		if request.content_type != 'application/json':
			return {"error": "Content must be in JSON format"}, HTTPStatus.UNSUPPORTED_MEDIA_TYPE

		data = request.get_json()
		receiver_username = data.get('receiver')
		subject = data.get('subject')
		body = data.get('body')
		
		if not all([receiver_username, subject, body]):
			return {"message": "Receiver, subject, and body are required"}, 400
			
		receiver = User.query.filter_by(username=receiver_username).first()
		if not receiver:
			return {"message": "Receiver not found"}, 404
			
		sender_username = get_jwt_identity()
		sender = User.query.filter_by(username=sender_username).first()

		new_mail = Mail(sender_id=sender.id, receiver_id=receiver.id, subject=subject, body=body)
		db.session.add(new_mail)
		db.session.commit()
		
		return {"message": "Mail sent successfully"}, 201

	@jwt_required()
	@swag_from('swagger/mail_get.yaml')
	def get(self):
		valid, auth_user_or_err, code = validate_api_key()
		if not valid:
			return auth_user_or_err, code

		username = get_jwt_identity()
		user = User.query.filter_by(username=username).first()
		
		mails = Mail.query.filter_by(receiver_id=user.id).all()
		return {"message": [m.to_dict() for m in mails]}, 200


class MailDetailResource(Resource):
	@jwt_required()
	@swag_from('swagger/mail_detail_get.yaml')
	def get(self, mail_id):
		valid, auth_user_or_err, code = validate_api_key()
		if not valid:
			return auth_user_or_err, code

		username = get_jwt_identity()
		user = User.query.filter_by(username=username).first()
		
		mail = Mail.query.get(mail_id)
		if not mail:
			return {"message": "Mail not found"}, 404
			
		if user.id not in [mail.sender_id, mail.receiver_id]:
			return {"message": "Unauthorized"}, 403
			
		return {"message": mail.to_dict(include_body=True)}, 200


	@jwt_required()
	@swag_from('swagger/mail_detail_delete.yaml')
	def delete(self, mail_id):
		valid, auth_user_or_err, code = validate_api_key()
		if not valid:
			return auth_user_or_err, code
			
		username = get_jwt_identity()
		user = User.query.filter_by(username=username).first()
		
		mail = Mail.query.get(mail_id)
		if not mail:
			return {"message": "Mail not found"}, 404
			
		
		if user.id not in [mail.sender_id, mail.receiver_id] and user.role != 'admin':
			return {"message": "Unauthorized"}, 403
			
		db.session.delete(mail)
		db.session.commit()
		
		return {"message": "Mail deleted successfully"}, 200


class AdminStatsResource(Resource):
	@jwt_required()
	@swag_from('swagger/admin_stats_get.yaml')
	def get(self):
		valid, auth_user_or_err, code = validate_api_key()
		if not valid:
			return auth_user_or_err, code

		if auth_user_or_err.role !='admin':
			return {"message": "Administrator access required"}, 403
		
		stats = {
			"total_users": User.query.count(),
			"total_mails": Mail.query.count()
		}
		return {"message": stats}, 200