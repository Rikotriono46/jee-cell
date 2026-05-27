import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set secret key for production
os.environ.setdefault('SECRET_KEY', 'jeecell-vercel-prod-2026')

from app import app

# Vercel expects the app object directly
application = app
