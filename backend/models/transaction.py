from backend.extensions import db
from datetime import datetime
from enum import Enum

class TransactionType(Enum):
    EARNING = "earning"
    POINT_WITHDRAWAL = "point_withdrawal"
    DEPOSIT = "deposit"
    REFERRAL_BONUS = "referral_bonus"
    CODE_REDEMPTION = "code_redemption"
    ADMIN_ADJUSTMENT = "admin_adjustment"

class TransactionStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.Enum(TransactionType), nullable=False)
    status = db.Column(db.Enum(TransactionStatus), default=TransactionStatus.COMPLETED)
    description = db.Column(db.String(255))
    amount = db.Column(db.Float, nullable=False)  # Can be positive or negative
    points_amount = db.Column(db.Float)  # Points involved in transaction
    currency = db.Column(db.String(3), default='USD')
    reference_id = db.Column(db.String(100))  # For linking to other entities
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='transactions')
    
    def __repr__(self):
        return f'<Transaction {self.type.value} ${self.amount}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type.value,
            'status': self.status.value,
            'description': self.description,
            'amount': self.amount,
            'points_amount': self.points_amount,
            'currency': self.currency,
            'reference_id': self.reference_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }