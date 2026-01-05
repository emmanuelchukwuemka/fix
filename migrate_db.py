import sqlite3
import os

def migrate():
    # Get the database path from environment variable or use default
    from backend.extensions import db
    from backend.app import create_app
    import backend.models.user
    import backend.models.task
    import backend.models.transaction
    import backend.models.support_message
    import backend.models.notification
    import backend.models.reward_code
    
    app = create_app()
    
    with app.app_context():
        # Create all tables and apply migrations
        db.create_all()
        print('Database tables created/updated successfully!')
        
        # For additional custom migrations, connect directly to the SQLite database
        project_root = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(project_root, 'instance', 'myfigpoint.db')
        
        # Ensure instance directory exists
        instance_dir = os.path.dirname(db_path)
        if not os.path.exists(instance_dir):
            os.makedirs(instance_dir)
        
        if not os.path.exists(db_path):
            print('Database not found at', db_path)
            print('Creating new database...')
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Tables to check for updated_at
        tables = ['users', 'tasks', 'user_tasks', 'transactions', 'support_messages', 'notifications', 'reward_codes']

        for table in tables:
            try:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in cursor.fetchall()]
                
                if 'updated_at' not in columns:
                    print(f"Adding updated_at to {table}...")
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN updated_at DATETIME")
                    cursor.execute(f"UPDATE {table} SET updated_at = CURRENT_TIMESTAMP")
                else:
                    print(f"updated_at already exists in {table}")
                    
            except Exception as e:
                print(f"Error checking table {table}: {e}")

        # Specific columns for users table
        try:
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            
            user_cols = {
                'country': 'VARCHAR(100)',
                'province': 'VARCHAR(100)',
                'routing_number': 'VARCHAR(50)',
                'swift_code': 'VARCHAR(50)',
                'account_type': 'VARCHAR(50)',
                'bank_address': 'VARCHAR(255)'
            }
            
            for col, col_type in user_cols.items():
                if col not in columns:
                    print(f"Adding {col} to users table...")
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
                else:
                    print(f"{col} already exists in users table")
                    
        except Exception as e:
            print(f"Error updating users table: {e}")

        # Specific columns for tasks table
        try:
            cursor.execute("PRAGMA table_info(tasks)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'requires_admin_verification' not in columns:
                print("Adding requires_admin_verification to tasks table...")
                cursor.execute("ALTER TABLE tasks ADD COLUMN requires_admin_verification BOOLEAN DEFAULT 0")
        except Exception as e:
            print(f"Error updating tasks table: {e}")

        # Specific columns for user_tasks table
        try:
            cursor.execute("PRAGMA table_info(user_tasks)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'proof_text' not in columns:
                print("Adding proof_text to user_tasks table...")
                cursor.execute("ALTER TABLE user_tasks ADD COLUMN proof_text TEXT")
            if 'proof_image' not in columns:
                print("Adding proof_image to user_tasks table...")
                cursor.execute("ALTER TABLE user_tasks ADD COLUMN proof_image VARCHAR(255)")
        except Exception as e:
            print(f"Error updating user_tasks table: {e}")

        conn.commit()
        conn.close()
        print("Migration complete!")

if __name__ == "__main__":
    migrate()