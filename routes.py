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
    """Run the HubSpot audit and display results"""
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
        
        # Run the audit
        audit_results = audit_engine.run_full_audit()
        
        if not audit_results:
            flash('Failed to run audit. Please check your HubSpot permissions.', 'error')
            return redirect(url_for('index'))
        
        # Store results in session for PDF generation
        session['audit_results'] = audit_results
        
        return render_template('dashboard.html', results=audit_results)
        
    except Exception as e:
        logging.error(f"Audit error: {str(e)}")
        flash('Error running audit. Please try again or check your HubSpot connection.', 'error')
        return redirect(url_for('index'))

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
