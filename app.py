#!/usr/bin/env python
"""
Entry point for MyFigPoint application
"""
import os
from backend.app import create_app

# Create app instance
app = create_app()

# Initialize database tables and seed data
with app.app_context():
    from backend.extensions import db
    db.create_all()
    
    # Also initialize with seed data if needed
    try:
        from backend.seed import seed_database
        seed_database()
    except ImportError:
        # Seed file doesn't exist or doesn't have seed_database function
        pass

# For Vercel deployment
if __name__ == '__main__' and os.environ.get('VERCEL') != '1':
    # Run dev server locally, not on deployment platforms
    if os.environ.get('RENDER') != 'true':
        app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

# Export the app for Vercel (this is needed for Vercel deployment)
try:
    app  # Make sure app is defined
except NameError:
    from backend.app import create_app
    app = create_app()