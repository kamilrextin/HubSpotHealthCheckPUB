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

def require_email_for_results(audit_results):
    """Email gate function - captures email before showing results"""
    
    # Check if user already provided email in this session
    if session.get('user_email'):
        # Save audit results to database
        return save_audit_results(session['user_email'], audit_results)
    
    # Show email capture form
    form = EmailCaptureForm()
    
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        company_name = form.company_name.data.strip() if form.company_name.data else None
        
        # Create or get user
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email, company_name=company_name)
            db.session.add(user)
            db.session.commit()
        
        # Store email in session
        session['user_email'] = email
        session['user_id'] = user.id
        
        # Save audit results
        audit_record = save_audit_results(email, audit_results)
        
        flash(f'Thanks! Your audit results are ready.', 'success')
        return redirect(url_for('show_results', audit_id=audit_record.id))
    
    # Store audit results temporarily in session for after email capture
    session['pending_audit_results'] = audit_results
    
    return render_template('email_gate.html', form=form)

def save_audit_results(email, audit_results):
    """Save audit results to database"""
    try:
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email)
            db.session.add(user)
            db.session.commit()
        
        # Create audit record
        audit_record = AuditResult(
            user_id=user.id,
            overall_score=audit_results.get('overall_score', 0),
            overall_grade=audit_results.get('overall_grade', 'F'),
            hubspot_portal_id=audit_results.get('portal_info', {}).get('portalId')
        )
        
        # Store full results as JSON
        audit_record.set_results_dict(audit_results)
        
        db.session.add(audit_record)
        db.session.commit()
        
        return audit_record
        
    except Exception as e:
        db.session.rollback()
        flash('Error saving audit results. Please try again.', 'error')
        return None