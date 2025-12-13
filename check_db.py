import sqlite3
import os

# Connect to the database
conn = sqlite3.connect('myfigpoint.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables in database:")
for table in tables:
    print(f"  {table[0]}")

# Check users table if it exists
try:
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    print(f"\nUsers table has {count} records")
    
    # Check specifically for admin user
    cursor.execute("SELECT email, role FROM users WHERE email = 'admin@myfigpoint.com'")
    result = cursor.fetchone()
    if result:
        print(f"\nAdmin user found in database:")
        print(f"  Email: {result[0]}")
        print(f"  Role: {result[1]}")
    else:
        print("\nAdmin user not found in database")
except Exception as e:
    print(f"\nError querying users table: {e}")

conn.close()