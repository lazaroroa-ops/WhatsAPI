from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Message



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