# PythonAnywhere WSGI configuration
# Edit path sesuai username kamu di PythonAnywhere

import sys
import os

# Ganti 'YOUR_USERNAME' dengan username PythonAnywhere kamu
project_home = '/home/YOUR_USERNAME/jee-cell'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment
os.environ['SECRET_KEY'] = 'your-secret-key-here'

from app import app as application
