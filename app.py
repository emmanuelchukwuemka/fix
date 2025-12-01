"""
WSGI entry point for MyFigPoint application
This file is used by gunicorn to serve the application
"""
from run import app

if __name__ == "__main__":
    app.run()