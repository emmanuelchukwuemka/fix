import sqlite3
import os

def migrate():
    # Try instance directory first, then root
    instance_db = os.path.join('instance', 'myfigpoint.db')
    root_db = 'myfigpoint.db'
    
    if os.path.exists(instance_db):
        db_path = instance_db
    elif os.path.exists(root_db):
        db_path = root_db
    else:
        print("Database not found in instance/ or root directory.")
        return

    print(f"Connecting to database at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # List of columns to add
    columns_to_add = [
        ('is_approved', 'BOOLEAN DEFAULT 0'),
        ('is_suspended', 'BOOLEAN DEFAULT 0'),
        ('is_verified', 'BOOLEAN DEFAULT 0'),
        ('verification_pending', 'BOOLEAN DEFAULT 0'),
        ('requires_admin_verification', 'BOOLEAN DEFAULT 0'),
        ('avatar_url', 'TEXT'),
        ('bank_name', 'TEXT'),
        ('account_name', 'TEXT'),
        ('account_number', 'TEXT'),
        ('routing_number', 'TEXT'),
        ('swift_code', 'TEXT'),
        ('account_type', 'TEXT'),
        ('bank_address', 'TEXT')
    ]

    for column_name, column_type in columns_to_add:
        try:
            print(f"Adding column {column_name}...")
            cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
            print(f"Column {column_name} added successfully.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"Column {column_name} already exists.")
            else:
                print(f"Error adding {column_name}: {e}")

    conn.commit()
    conn.close()
    print("Migration completed.")

if __name__ == "__main__":
    migrate()