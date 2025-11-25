from backend.app import db
from datetime import datetime
from enum import Enum

class UserRole(Enum):
    USER = "user"
    PARTNER = "partner"
    ADMIN = "admin"

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.USER, nullable=False)
    phone = db.Column(db.String(20))
    bank_name = db.Column(db.String(100))
    account_name = db.Column(db.String(100))
    account_number = db.Column(db.String(50))
    referral_code = db.Column(db.String(20), unique=True)
    referred_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    points_balance = db.Column(db.Float, default=0.0)
    total_points_earned = db.Column(db.Float, default=0.0)
    total_points_withdrawn = db.Column(db.Float, default=0.0)
    total_earnings = db.Column(db.Float, default=0.0)
    total_withdrawn = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    referred_users = db.relationship('User', backref=db.backref('referrer', remote_side=[id]))
    transactions = db.relationship('Transaction', back_populates='user')
    codes = db.relationship('RewardCode', back_populates='user')
    
    def __repr__(self):
        return f'<User {self.full_name} ({self.email})>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'role': self.role.value,
            'phone': self.phone,
            'bank_name': self.bank_name,
            'account_name': self.account_name,
            'account_number': self.account_number,
            'referral_code': self.referral_code,
            'referred_by': self.referred_by,
            'points_balance': self.points_balance,
            'total_points_earned': self.total_points_earned,
            'total_points_withdrawn': self.total_points_withdrawn,
            'total_earnings': self.total_earnings,
            'total_withdrawn': self.total_withdrawn,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }