from backend.app import db
from datetime import datetime

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    reward_amount = db.Column(db.Float, default=0.0)
    points_reward = db.Column(db.Float, default=0.0)
    category = db.Column(db.String(50))  # Daily, Survey, Video, etc.
    time_required = db.Column(db.Integer)  # Minutes
    is_active = db.Column(db.Boolean, default=True)
    requires_admin_verification = db.Column(db.Boolean, default=False)  # New field for admin verification
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Task {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'reward_amount': self.reward_amount,
            'points_reward': self.points_reward,
            'category': self.category,
            'time_required': self.time_required,
            'is_active': self.is_active,
            'requires_admin_verification': self.requires_admin_verification,  # Include in dict
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class UserTask(db.Model):
    __tablename__ = 'user_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    status = db.Column(db.String(20), default='available')  # available, in_progress, completed, pending_review, rejected
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User')
    task = db.relationship('Task')
    
    def __repr__(self):
        return f'<UserTask User:{self.user_id} Task:{self.task_id} Status:{self.status}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'task_id': self.task_id,
            'status': self.status,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }