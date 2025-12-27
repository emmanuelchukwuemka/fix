from backend.extensions import db
from datetime import datetime
from enum import Enum

class MessageType(Enum):
    USER_TO_SUPPORT = "user_to_support"
    SUPPORT_TO_USER = "support_to_user"

class MessageStatus(Enum):
    SENT = "sent"
    READ = "read"
    REPLIED = "replied"
    CLOSED = "closed"

class SupportMessage(db.Model):
    __tablename__ = 'support_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text)
    message_type = db.Column(db.Enum(MessageType), nullable=False)
    status = db.Column(db.Enum(MessageStatus), default=MessageStatus.SENT)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User')
    
    def __repr__(self):
        return f'<SupportMessage {self.subject}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'subject': self.subject,
            'message': self.message,
            'response': self.response,
            'message_type': self.message_type.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }