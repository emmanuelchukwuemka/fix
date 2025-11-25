from backend.app import create_app, db, bcrypt
from backend.models.user import User, UserRole
from backend.models.reward_code import RewardCode
from backend.models.task import Task
from backend.utils.helpers import generate_reward_code, generate_referral_code
import random

def seed_database():
    app = create_app()
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Check if admin user already exists
        admin = User.query.filter_by(email='admin@myfigpoint.com').first()
        if not admin:
            # Create admin user
            admin = User(
                full_name='Admin User',
                email='admin@myfigpoint.com',
                password_hash=bcrypt.generate_password_hash('admin123').decode('utf-8'),
                role=UserRole.ADMIN,
                referral_code=generate_referral_code()
            )
            db.session.add(admin)
            print("Created admin user")
        
        # Create sample users
        users = []
        for i in range(10):
            user = User(
                full_name=f'User {i+1}',
                email=f'user{i+1}@example.com',
                password_hash=bcrypt.generate_password_hash('password123').decode('utf-8'),
                role=UserRole.USER,
                referral_code=generate_referral_code(),
                points_balance=random.uniform(100, 5000),
                total_points_earned=random.uniform(500, 10000),
                total_earnings=random.uniform(50, 500)
            )
            db.session.add(user)
            users.append(user)
        
        # Create sample reward codes
        codes = []
        for i in range(50):
            code = RewardCode(
                code=generate_reward_code(),
                point_value=round(random.uniform(0.1, 5.0), 2),
                is_used=random.choice([True, False])
            )
            if code.is_used:
                code.used_by = random.choice(users).id
            db.session.add(code)
            codes.append(code)
        
        # Create sample tasks
        tasks_data = [
            {
                'title': 'Complete Health Survey',
                'description': 'Share your opinion on wellness products (10-15 min)',
                'money_reward': 8.0,
                'points_reward': 80.0,
                'category': 'Survey',
                'time_required': 12
            },
            {
                'title': 'Daily Login Bonus',
                'description': 'Just log in to claim your free points!',
                'money_reward': 2.0,
                'points_reward': 20.0,
                'category': 'Daily',
                'time_required': 1
            },
            {
                'title': 'Install & Play Mobile Game',
                'description': 'Reach level 10 in "Rise of Kingdoms" (New users only)',
                'money_reward': 25.0,
                'points_reward': 250.0,
                'category': 'Limited Time',
                'time_required': 30
            },
            {
                'title': 'Watch Video Ads (5x)',
                'description': 'Watch short ads and earn instantly',
                'money_reward': 3.5,
                'points_reward': 35.0,
                'category': 'Videos',
                'time_required': 5
            },
            {
                'title': 'Invite a Friend',
                'description': 'They join → You both get bonus points!',
                'money_reward': 10.0,
                'points_reward': 100.0,
                'category': 'Referral',
                'time_required': 2
            }
        ]
        
        for task_data in tasks_data:
            task = Task(**task_data)
            db.session.add(task)
        
        db.session.commit()
        print("Database seeded successfully!")

if __name__ == '__main__':
    seed_database()