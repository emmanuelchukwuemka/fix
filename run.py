#!/usr/bin/env python
"""
Entry point for MyFigPoint application
"""
import os
from backend.app import create_app

# For Vercel compatibility
app = create_app()

if __name__ == '__main__':
    # Only run dev server locally, not on Vercel
    if os.environ.get('VERCEL') != '1':
        app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))