import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import create_app
from backend.extensions import db, bcrypt
from backend.models.user import User, UserRole

def test_admin_login():
    app = create_app()
    
    with app.app_context():
        # Check if admin user exists
        admin = User.query.filter_by(email='admin@myfigpoint.com').first()
        if not admin:
            print("Admin user does not exist!")
            return
            
        print(f"Admin user found:")
        print(f"  Email: {admin.email}")
        print(f"  Role: {admin.role.value}")
        print(f"  Password hash: {admin.password_hash}")
        
        # Test password
        password = 'MyFigPoint2025'
        is_correct = bcrypt.check_password_hash(admin.password_hash, password)
        print(f"Password '{password}' is correct: {is_correct}")
        
        # If password is incorrect, update it
        if not is_correct:
            print("Updating password...")
            admin.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            db.session.commit()
            print("Password updated successfully!")
            
            # Verify again
            is_correct = bcrypt.check_password_hash(admin.password_hash, password)
            print(f"Password '{password}' is now correct: {is_correct}")

if __name__ == '__main__':
    test_admin_login()