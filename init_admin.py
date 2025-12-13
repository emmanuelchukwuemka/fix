import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import create_app
from backend.extensions import db, bcrypt
from backend.models.user import User, UserRole
from backend.utils.helpers import generate_referral_code

def init_admin():
    app = create_app()
    
    with app.app_context():
        # Create all tables
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
            db.session.commit()
            print("Admin user created successfully!")
            print("Email: admin@myfigpoint.com")
            print("Password: MyFigPoint2025")
        else:
            print("Admin user already exists")
            print("Email:", admin.email)
            print("Role:", admin.role.value)

if __name__ == '__main__':
    init_admin()