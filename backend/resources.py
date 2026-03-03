from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Mail



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