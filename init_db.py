#!/usr/bin/env python
"""
Database initialization script for MyFigPoint
"""
from backend.app import create_app, db
from backend.seed import seed_database

def init_database():
    """Initialize the database and seed it with sample data"""
    app = create_app()
    
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully!")
        
        # Seed the database
        print("Seeding database with sample data...")
        seed_database()
        print("Database seeding completed!")

if __name__ == '__main__':
    init_database()
    print("\nDatabase initialization complete!")
    print("You can now run the application with: python run.py")