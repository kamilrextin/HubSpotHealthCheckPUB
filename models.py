from app import db
from datetime import datetime
import json

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    company_name = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to audit results
    audit_results = db.relationship('AuditResult', backref='user', lazy=True)

class AuditResult(db.Model):
    __tablename__ = 'audit_results'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Store audit data as JSON
    results_json = db.Column(db.Text, nullable=False)  # JSON string of audit results
    overall_score = db.Column(db.Float, nullable=True)
    overall_grade = db.Column(db.String(2), nullable=True)
    
    # Metadata
    hubspot_portal_id = db.Column(db.String(255), nullable=True)
    audit_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # AI enhancements
    ai_summary = db.Column(db.Text, nullable=True)  # AI-generated summary
    ai_recommendations = db.Column(db.Text, nullable=True)  # AI-generated recommendations
    
    def get_results_dict(self):
        """Convert JSON string back to dictionary"""
        return json.loads(self.results_json) if self.results_json else {}
    
    def set_results_dict(self, results_dict):
        """Convert dictionary to JSON string"""
        self.results_json = json.dumps(results_dict)