# Vercel serverless function entry point
import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import the Flask app
from web.app import app

# Configure the app for production
app.debug = False
app.config['TESTING'] = False

# Export the Flask app directly - Vercel will handle the WSGI conversion
app
