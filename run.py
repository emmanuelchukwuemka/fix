#!/usr/bin/env python
"""
Entry point for MyFigPoint application
"""
import os
from backend.app import create_app

# Create app instance
app = create_app()

# Initialize database tables
with app.app_context():
    from backend.app import db
    db.create_all()

if __name__ == '__main__':
    # Run dev server locally, not on deployment platforms
    if os.environ.get('VERCEL') != '1' and os.environ.get('RENDER') != 'true':
        app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))