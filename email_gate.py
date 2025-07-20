#!/usr/bin/env python3
"""Email gate functionality for lead capture before audit results"""

from flask import request, session, flash, redirect, url_for, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from models import User, AuditResult, db
import json

class EmailCaptureForm(FlaskForm):
    email = EmailField('Email Address', validators=[DataRequired(), Email()])
    company_name = StringField('Company Name (Optional)', validators=[Length(max=255)])
    submit = SubmitField('View My Audit Results')

# Removed require_email_for_results - logic moved to routes.py

def save_audit_results(email, audit_results):
    """Save audit results to database"""
    try:
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email)
            db.session.add(user)
            db.session.commit()
        
        # Create audit record
        audit_record = AuditResult()
        audit_record.user_id = user.id
        audit_record.overall_score = audit_results.get('overall_score', 0)
        audit_record.overall_grade = audit_results.get('overall_grade', 'F')
        audit_record.hubspot_portal_id = audit_results.get('portal_info', {}).get('portalId')
        
        # Store full results as JSON
        audit_record.set_results_dict(audit_results)
        
        db.session.add(audit_record)
        db.session.commit()
        
        return audit_record
        
    except Exception as e:
        db.session.rollback()
        flash('Error saving audit results. Please try again.', 'error')
        return None