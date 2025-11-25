#!/usr/bin/env python
"""
Entry point for MyFigPoint application
"""
import os
from dev_server import main
from backend.app import create_app

# For Vercel compatibility
app = create_app()

if __name__ == '__main__':
    main()