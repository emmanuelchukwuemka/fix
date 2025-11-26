"""
WSGI entry point for Vercel deployment
"""
from run import app

# Vercel expects an 'app' object
application = app

# For local testing
if __name__ == "__main__":
    app.run()