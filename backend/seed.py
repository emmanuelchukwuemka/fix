from backend.app import create_app
from backend.extensions import db, bcrypt
from backend.models.user import User, UserRole
from backend.models.reward_code import RewardCode
from backend.models.task import Task
from backend.models.notification import Notification, NotificationType
from backend.models.support_message import SupportMessage, MessageType, MessageStatus
from backend.utils.helpers import generate_reward_code, generate_referral_code
import random

def seed_database():
    app = create_app()
    
    with app.app_context():
        # Initialize database tables if they don't exist
        from backend.app import db
        db.create_all()
        # Create tables
        db.create_all()
        
        # Check if admin user already exists
        admin = User.query.filter_by(email='admin@myfigpoint.com').first()
        if not admin:
            # Create admin user with the exact credentials specified
            admin = User(
                full_name='Admin User',
                email='admin@myfigpoint.com',
                password_hash=bcrypt.generate_password_hash('MyFigPoint2025').decode('utf-8'),
                role=UserRole.ADMIN,
                referral_code=generate_referral_code()
            )
            db.session.add(admin)
            print("Created admin user")
        else:
            print("Admin user already exists")
        
        db.session.commit()
        print("Database seeded successfully!")

if __name__ == '__main__':
    seed_database()
    print("Database seeded successfully! You can now log in with:")
    print("Email: admin@myfigpoint.com")
    print("Password: MyFigPoint2025")