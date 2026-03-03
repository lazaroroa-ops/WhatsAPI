from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Mail

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


class MessageResource(Resource):
	@jwt_required()
	def post(self):
		#Posiblemente añadir api key para confirmar user
		data = request.get_json()
		receiver_username = data.get('receiver')
		content = data.get('content')
		
		if not receiver_username or not content:
			return {"message": "Receiver and content are required"}, 400
			
		receiver = User.query.filter_by(username=receiver_username).first()
		if not receiver:
			return {"message": "Receiver not found"}, 404
			
		sender_username = get_jwt_identity()
		sender = User.query.filter_by(username=sender_username).first()
		
		#TODO otra vez key para confirmar sender

		new_message = Message(sender_id=sender.id, receiver_id=receiver.id, content=content)
		db.session.add(new_message)
		db.session.commit()
		
		return {"message": "Message sent successfully"}, 201

	@jwt_required()
	def get(self):

		username = get_jwt_identity()
		print(username)
		user = User.query.filter_by(username=username).first()

		messages = Message.query.filter((Message.sender_id == user.id) | (Message.receiver_id == user.id)).all()
		return [msg.to_dict() for msg in messages], 200

class MessageDetailResource(Resource):
	@jwt_required()
	def put(self, message_id):
		#api again
			
		username = get_jwt_identity()
		user = User.query.filter_by(username=username).first()
		
		#same

		message = Message.query.get(message_id)
		if not message:
			return {"message": "Message not found"}, 404
			
		if message.sender_id != user.id:
			return {"message": "Only the sender can edit the message"}, 403
			
		data = request.get_json()
		if not data or 'content' not in data:
			return {"message": "Content is required"}, 400
			
		message.content = data.get('content')
		db.session.commit()
		
		return {"message": "Message updated successfully"}, 200

	@jwt_required()
	def delete(self, message_id):
		
		username = get_jwt_identity()
		user = User.query.filter_by(username=username).first()

		message = Message.query.get(message_id)
		if not message:
			return {"message": "Message not found"}, 404
			
		
		if user.id not in [message.sender_id, message.receiver_id] and user.role != 'admin':
			return {"message": "Not authorized to delete this message"}, 403
			
		db.session.delete(message)
		db.session.commit()
		
		return {"message": "Message deleted successfully"}, 200


class ChangePassResource(Resource):
	@jwt_required()
	def put(self):
		#api again
		
		username = get_jwt_identity()
		user = User.query.filter_by(username=username).first()
		
		#same

		data = request.get_json()
		old_password = data.get('old_password')
		new_password = data.get('new_password')

		try:
			password_schema.load(dict(password=new_password))
		except ValidationError as e:
			return {'error': e.messages}, 400

		if not old_password or not new_password:
			return {"message": "Old and new passwords are required"}, 400

		if not check_password_hash(user.password, old_password):
			return {"message": "Old password is not correct"}, 401
			
		user.password = generate_password_hash(new_password)
		db.session.commit()
		
		return {"message": "Password updated successfully"}, 200


class DeleteAccountResource(Resource):
	@jwt_required()
	def delete(self):
		#api again
		
		username = get_jwt_identity()
		user = User.query.filter_by(username=username).first()
		
		#same

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
    def post(self):
        #Posiblemente añadir api key para confirmar user
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
    def get(self):
        username = get_jwt_identity()
        user = User.query.filter_by(username=username).first()
        

        mails = Mail.query.filter_by(receiver_id=user.id).all()
        return [m.to_dict() for m in mails], 200

class MailDetailResource(Resource):
    @jwt_required()
    def get(self, mail_id):
        username = get_jwt_identity()
        user = User.query.filter_by(username=username).first()
        
        mail = Mail.query.get(mail_id)
        if not mail:
            return {"message": "Mail not found"}, 404
            
        
        if user.id not in [mail.sender_id, mail.receiver_id]:
            return {"message": "Unauthorized"}, 403
            
        return mail.to_dict(include_body=True), 200

    @jwt_required()
    def delete(self, mail_id):
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
