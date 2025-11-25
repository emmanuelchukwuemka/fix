"""
WSGI entry point for Vercel deployment
"""
from dev_server import app, initialize_database

# Initialize database on startup
initialize_database()

# Vercel expects an 'app' object
application = app