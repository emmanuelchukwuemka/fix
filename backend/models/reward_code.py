from backend.extensions import db
from datetime import datetime

class RewardCode(db.Model):
    __tablename__ = 'reward_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), unique=True, nullable=False)  # 5 letters + 3 numbers
    point_value = db.Column(db.Float, nullable=False)  # Points awarded per code
    is_used = db.Column(db.Boolean, default=False)
    used_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # User who redeemed the code
    used_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    batch_id = db.Column(db.String(50))  # To group codes from the same batch
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='codes')
    
    def __repr__(self):
        return f'<RewardCode {self.code}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'point_value': self.point_value,
            'is_used': self.is_used,
            'used_by': self.used_by,
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'batch_id': self.batch_id
        }