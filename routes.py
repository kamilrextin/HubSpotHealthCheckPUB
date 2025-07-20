import os
import logging
from flask import render_template, request, redirect, url_for, session, flash, make_response, send_file
from app import app
from hubspot_service import HubSpotService
from audit_engine import AuditEngine
from pdf_generator import PDFGenerator

@app.route('/')
def index():
    """Home page with audit initiation"""
    return render_template('index.html')

@app.route('/token-auth', methods=['GET', 'POST'])
def token_auth():
    """Direct token authentication for users who already have access tokens"""
    if request.method == 'POST':
        token = request.form.get('access_token')
        if token:
            # Store token in session
            session['hubspot_token'] = token
            flash('Access token saved successfully!', 'success')
            return redirect(url_for('run_audit'))
        else:
            flash('Please provide a valid access token', 'error')
    
    return render_template('token_auth.html')

@app.route('/scoring-methodology')
def scoring_methodology():
    """Display the scoring methodology page"""
    return render_template('scoring_methodology.html')

@app.route('/oauth/setup')
def oauth_setup():
    """OAuth setup guide for users"""
    return render_template('oauth_setup.html')

@app.route('/oauth/authorize')
def oauth_authorize():
    """Redirect to HubSpot OAuth authorization"""
    try:
        # Check if OAuth credentials are configured
        client_id = app.config.get('HUBSPOT_CLIENT_ID')
        client_secret = app.config.get('HUBSPOT_CLIENT_SECRET')
        
        logging.debug(f"OAuth authorize called - Client ID exists: {bool(client_id)}, Client Secret exists: {bool(client_secret)}")
        
        if not client_id or not client_secret:
            flash('OAuth is not configured. Please set up your HubSpot app credentials first.', 'error')
            return redirect(url_for('oauth_setup'))
        
        hubspot = HubSpotService()
        auth_url = hubspot.get_authorization_url()
        
        logging.debug(f"Generated auth URL: {auth_url}")
        
        return redirect(auth_url)
    except Exception as e:
        logging.error(f"OAuth authorization error: {str(e)}")
        flash(f'Error initiating HubSpot authentication: {str(e)}', 'error')
        return redirect(url_for('oauth_setup'))

@app.route('/oauth/callback')
def oauth_callback():
    """Handle OAuth callback from HubSpot"""
    try:
        code = request.args.get('code')
        error = request.args.get('error')
        
        if error:
            error_description = request.args.get('error_description', 'No description provided')
            logging.error(f"OAuth error: {error} - {error_description}")
            flash(f'HubSpot authentication failed: {error}. {error_description}', 'error')
            return redirect(url_for('index'))
        
        if not code:
            flash('No authorization code received from HubSpot', 'error')
            return redirect(url_for('index'))
        
        hubspot = HubSpotService()
        token_data = hubspot.exchange_code_for_token(code)
        
        if not token_data:
            flash('Failed to obtain access token from HubSpot', 'error')
            return redirect(url_for('index'))
        
        # Store token in session
        session['hubspot_token'] = token_data['access_token']
        session['hubspot_refresh_token'] = token_data.get('refresh_token')
        session['hubspot_expires_in'] = token_data.get('expires_in')
        
        flash('Successfully connected to HubSpot!', 'success')
        return redirect(url_for('run_audit'))
        
    except Exception as e:
        logging.error(f"OAuth callback error: {str(e)}")
        flash('Error processing HubSpot authentication. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/audit')
def run_audit():
    """Run the HubSpot audit and display results with email gate"""
    try:
        # Check if user is authenticated
        if 'hubspot_token' not in session:
            flash('Please authenticate with HubSpot first', 'warning')
            return redirect(url_for('index'))
        
        hubspot = HubSpotService(session['hubspot_token'])
        audit_engine = AuditEngine(hubspot)
        
        # Debug: Test workflow fetching directly
        logging.debug("=== Testing workflow API directly ===")
        workflows_direct = hubspot.get_workflows()
        logging.debug(f"Direct workflow API test found: {len(workflows_direct)} workflows")
        if workflows_direct:
            logging.debug(f"First workflow sample: {workflows_direct[0].keys() if workflows_direct else 'None'}")
        
        # Run the enhanced audit
        audit_results = audit_engine.run_full_audit()
        
        if not audit_results:
            flash('Failed to run audit. Please check your HubSpot permissions.', 'error')
            return redirect(url_for('index'))
        
        # Store results in session for potential full report access
        session['audit_results'] = audit_results
        
        # Show basic results immediately (no email required)
        return render_template('dashboard.html', results=audit_results, show_preview=True)
        
    except Exception as e:
        logging.error(f"Audit error: {str(e)}")
        flash('Error running audit. Please try again or check your HubSpot connection.', 'error')
        return redirect(url_for('index'))

@app.route('/results/<int:audit_id>')
def show_results(audit_id):
    """Show audit results after email capture"""
    try:
        from models import AuditResult
        audit_record = AuditResult.query.get_or_404(audit_id)
        
        # Check if user has access (either same session or same email)
        user_email = session.get('user_email')
        if not user_email or audit_record.user.email != user_email:
            flash('Access denied to these audit results', 'error')
            return redirect(url_for('index'))
        
        results = audit_record.get_results_dict()
        return render_template('dashboard.html', results=results, audit_record=audit_record, show_preview=False)
        
    except Exception as e:
        logging.error(f"Results display error: {str(e)}")
        flash('Error displaying results', 'error')
        return redirect(url_for('index'))

@app.route('/unlock_full_report', methods=['POST'])
def unlock_full_report():
    """Handle email submission to unlock full AI-enhanced report"""
    try:
        email = request.form.get('email', '').lower().strip()
        if not email:
            flash('Please enter a valid email address', 'error')
            return redirect(request.referrer or url_for('index'))
        
        from models import User, AuditResult, db
        
        # Create or get user
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User()
            user.email = email
            db.session.add(user)
            db.session.commit()
        
        # Store email in session
        session['user_email'] = email
        session['user_id'] = user.id
        
        # Get audit results from session
        audit_results = session.get('audit_results')
        if not audit_results:
            flash('No audit results found. Please run a new audit.', 'warning')
            return redirect(url_for('index'))
        
        # Add AI enhancements now that user provided email
        from ai_analyzer import AIAnalyzer
        ai_analyzer = AIAnalyzer()
        ai_enhancements = ai_analyzer.generate_comprehensive_report(audit_results)
        audit_results.update(ai_enhancements)
        
        # Save enhanced results to database
        audit_record = AuditResult()
        audit_record.user_id = user.id
        audit_record.overall_score = audit_results.get('overall_score', 0)
        audit_record.overall_grade = audit_results.get('overall_grade', 'F')
        audit_record.set_results_dict(audit_results)
        db.session.add(audit_record)
        db.session.commit()
        
        # Update session with enhanced results
        session['audit_results'] = audit_results
        
        flash('Thanks! Your complete AI-enhanced report is ready.', 'success')
        return redirect(url_for('show_results', audit_id=audit_record.id))
        
    except Exception as e:
        logging.error(f"Unlock report error: {str(e)}")
        flash('Error processing your request. Please try again.', 'error')
        return redirect(request.referrer or url_for('index'))

@app.route('/email_capture', methods=['GET', 'POST'])
def email_capture():
    """Handle email capture form submission"""
    from email_gate import EmailCaptureForm
    from models import User, AuditResult, db
    
    form = EmailCaptureForm()
    
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        company_name = form.company_name.data.strip() if form.company_name.data else None
        
        # Create or get user
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User()
            user.email = email
            user.company_name = company_name
            db.session.add(user)
            db.session.commit()
        
        # Store email in session
        session['user_email'] = email
        session['user_id'] = user.id
        
        # Get pending results from session
        pending_results = session.get('pending_audit_results')
        if pending_results:
            # Save audit results
            audit_record = AuditResult()
            audit_record.user_id = user.id
            audit_record.overall_score = pending_results.get('overall_score', 0)
            audit_record.overall_grade = pending_results.get('overall_grade', 'F')
            audit_record.set_results_dict(pending_results)
            db.session.add(audit_record)
            db.session.commit()
            
            # Clean up session
            session.pop('pending_audit_results', None)
            
            flash('Thanks! Your audit results are ready.', 'success')
            return redirect(url_for('show_results', audit_id=audit_record.id))
        else:
            flash('No pending audit results found. Please run a new audit.', 'warning')
            return redirect(url_for('index'))
    
    return render_template('email_gate.html', form=form)

@app.route('/export/pdf')
def export_pdf():
    """Generate and download PDF report"""
    try:
        if 'audit_results' not in session:
            flash('No audit results found. Please run an audit first.', 'warning')
            return redirect(url_for('index'))
        
        audit_results = session['audit_results']
        pdf_generator = PDFGenerator()
        
        # Generate PDF
        pdf_buffer = pdf_generator.generate_report(audit_results)
        
        # Create response
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=hubspot_audit_report.pdf'
        
        return response
        
    except Exception as e:
        logging.error(f"PDF export error: {str(e)}")
        flash('Error generating PDF report. Please try again.', 'error')
        return redirect(url_for('run_audit'))

@app.route('/logout')
def logout():
    """Clear session and logout"""
    session.clear()
    flash('Successfully logged out', 'info')
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', 
                         error_title='Page Not Found',
                         error_message='The page you are looking for does not exist.'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html',
                         error_title='Internal Server Error',
                         error_message='Something went wrong on our end. Please try again.'), 500
