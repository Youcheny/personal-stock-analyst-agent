# Vercel serverless function entry point
import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import the Flask app
from web.app import app

# Export the app for Vercel
app.debug = False
app.config['TESTING'] = False

# This is what Vercel expects
handler = app
