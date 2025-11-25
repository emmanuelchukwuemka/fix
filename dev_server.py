#!/usr/bin/env python
"""
Development server script for MyFigPoint
This script initializes the database and starts the Flask development server
"""
import os
import sys
from backend.app import create_app, db
from backend.seed import seed_database

def main():
    print("Starting MyFigPoint Development Server...")
    
    # Create the Flask app
    app = create_app()
    
    # Initialize database if it doesn't exist
    with app.app_context():
        print("Initializing database...")
        db.create_all()
        
        # Check if we have any users, if not seed the database
        from backend.models.user import User
        user_count = User.query.count()
        if user_count == 0:
            print("Seeding database with sample data...")
            seed_database()
    
    print("\n" + "="*50)
    print("MyFigPoint Development Server")
    print("="*50)
    print("Frontend: http://localhost:5000")
    print("Backend API: http://localhost:5000/api")
    print("Press CTRL+C to stop the server")
    print("="*50)
    
    # Run the development server
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()