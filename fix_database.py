import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import create_app
from backend.extensions import db, bcrypt
from backend.models.user import User, UserRole
from backend.models.reward_code import RewardCode
from backend.models.task import Task
from backend.models.notification import Notification
from backend.models.support_message import SupportMessage
from backend.models.password_reset import PasswordResetToken
from backend.models.transaction import Transaction
from backend.utils.helpers import generate_referral_code, generate_reward_code

def fix_database():
    app = create_app()
    
    with app.app_context():
        # Drop all tables first to ensure clean state
        print("Dropping existing tables...")
        db.drop_all()
        
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully!")
        
        # Check if admin user already exists
        admin = User.query.filter_by(email='admin@myfigpoint.com').first()
        if not admin:
            print("Creating admin user...")
            # Create admin user with the exact credentials specified
            admin = User(
                full_name='Admin User',
                email='admin@myfigpoint.com',
                password_hash=bcrypt.generate_password_hash('MyFigPoint2025').decode('utf-8'),
                role=UserRole.ADMIN,
                referral_code=generate_referral_code()
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully!")
        else:
            print("Admin user already exists")
            # Ensure the password is correct
            password = 'MyFigPoint2025'
            if not bcrypt.check_password_hash(admin.password_hash, password):
                print("Updating admin password...")
                admin.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
                db.session.commit()
                print("Admin password updated successfully!")
        
        print("Database initialization complete!")

if __name__ == '__main__':
    fix_database()