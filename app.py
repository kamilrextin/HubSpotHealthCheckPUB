import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Database setup
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db.init_app(app)

# HubSpot OAuth configuration
app.config['HUBSPOT_CLIENT_ID'] = os.environ.get("HUBSPOT_CLIENT_ID")
app.config['HUBSPOT_CLIENT_SECRET'] = os.environ.get("HUBSPOT_CLIENT_SECRET")
app.config['HUBSPOT_REDIRECT_URI'] = os.environ.get("HUBSPOT_REDIRECT_URI", "https://hubspotaudit.replit.app/oauth/callback")

# Create database tables
with app.app_context():
    import models  # noqa: F401
    db.create_all()
    logging.info("Database tables created")

# Import routes after app creation to avoid circular imports
from routes import *
