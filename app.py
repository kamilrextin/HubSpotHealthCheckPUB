import os
import logging
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# HubSpot OAuth configuration
app.config['HUBSPOT_CLIENT_ID'] = os.environ.get("HUBSPOT_CLIENT_ID")
app.config['HUBSPOT_CLIENT_SECRET'] = os.environ.get("HUBSPOT_CLIENT_SECRET")
# Set redirect URI for Replit environment
app.config['HUBSPOT_REDIRECT_URI'] = os.environ.get("HUBSPOT_REDIRECT_URI", "https://workspace.kamilrextin.replit.app/oauth/callback")

# Import routes after app creation to avoid circular imports
from routes import *
