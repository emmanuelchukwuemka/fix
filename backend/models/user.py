from backend.extensions import db
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
    daily_code_requirement = db.Column(db.Integer, default=5)  # 5 or 10 codes per day
    is_approved = db.Column(db.Boolean, default=False)  # For partner account approval
    is_suspended = db.Column(db.Boolean, default=False)  # For account suspension
    is_verified = db.Column(db.Boolean, default=False)  # For verified status
    verification_pending = db.Column(db.Boolean, default=False)  # For pending verification
    avatar_url = db.Column(db.String(255))  # User avatar URL
    country = db.Column(db.String(100))
    province = db.Column(db.String(100))
    routing_number = db.Column(db.String(50))
    swift_code = db.Column(db.String(50))
    account_type = db.Column(db.String(50), default="savings")
    bank_address = db.Column(db.String(255))
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
            'role': self.role.value if hasattr(self.role, 'value') else self.role,
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
            'daily_code_requirement': self.daily_code_requirement,
            'is_approved': self.is_approved,
            'is_suspended': self.is_suspended,
            'is_verified': self.is_verified,
            'verification_pending': self.verification_pending,
            'avatar_url': self.avatar_url,
            'country': self.country,
            'province': self.province,
            'routing_number': self.routing_number,
            'swift_code': self.swift_code,
            'account_type': self.account_type,
            'bank_address': self.bank_address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }