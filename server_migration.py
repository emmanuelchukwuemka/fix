import sqlite3
import os

def migrate():
    # Use the server's database path
    db_path = '/var/www/myfigpoint/instance/myfigpoint.db'
    
    if not os.path.exists(db_path):
        print("Database not found at", db_path)
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Add missing columns to users table
    try:
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add avatar_url column if it doesn't exist
        if 'avatar_url' not in columns:
            print("Adding avatar_url to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN avatar_url VARCHAR(255)")
        else:
            print("avatar_url already exists in users table")
            
        # Add other columns that may be missing
        user_cols = {
            'country': 'VARCHAR(100)',
            'province': 'VARCHAR(100)',
            'routing_number': 'VARCHAR(50)',
            'swift_code': 'VARCHAR(50)',
            'account_type': 'VARCHAR(50)',
            'bank_address': 'VARCHAR(255)',
            'updated_at': 'DATETIME'
        }
        
        for col, col_type in user_cols.items():
            if col not in columns:
                print(f"Adding {col} to users table...")
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
            else:
                print(f"{col} already exists in users table")
                
    except Exception as e:
        print(f"Error updating users table: {e}")

    # Add missing columns to tasks table
    try:
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'requires_admin_verification' not in columns:
            print("Adding requires_admin_verification to tasks table...")
            cursor.execute("ALTER TABLE tasks ADD COLUMN requires_admin_verification BOOLEAN DEFAULT 0")
        else:
            print("requires_admin_verification already exists in tasks table")
    except Exception as e:
        print(f"Error updating tasks table: {e}")

    # Add missing columns to user_tasks table
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