import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import create_app
from backend.extensions import db
from backend.models.user import User

def check_database():
    app = create_app()
    
    with app.app_context():
        # Get the database URI
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        print(f"Database URI: {db_uri}")
        
        # Check if tables exist
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"Tables in database: {tables}")
        
        # Check users table
        if 'users' in tables:
            user_count = User.query.count()
            print(f"Users table has {user_count} records")
            
            # Check specifically for admin user
            admin = User.query.filter_by(email='admin@myfigpoint.com').first()
            if admin:
                print(f"\nAdmin user found:")
                print(f"  Email: {admin.email}")
                print(f"  Role: {admin.role.value}")
            else:
                print("\nAdmin user not found in database")
        else:
            print("\nUsers table does not exist")

if __name__ == '__main__':
    check_database()