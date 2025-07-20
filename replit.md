# HubSpot Marketing Operations Audit Tool

## Overview

This is a Flask-based web application that performs comprehensive audits of HubSpot marketing operations. The tool connects to HubSpot via OAuth 2.0 authentication, analyzes various aspects of a HubSpot instance, and provides scored assessments with actionable recommendations. Users can view results in a web dashboard and export detailed PDF reports.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes (July 2025)

### Forms Grading Enhancement (July 20, 2025)
- **Sophisticated Usage-Based Analysis**: Forms now graded based on actual usage data rather than just existence
- **30-Day Submission Tracking**: Analyzes form submissions over last 30 days to identify unused forms
- **Field Consolidation Detection**: Identifies common field sets across forms to highlight consolidation opportunities
- **Enhanced Scoring Algorithm**: Adjusts scores based on actual form performance (submissions vs zero usage)
- **Improved Recommendations**: Provides specific actionable advice based on usage patterns
- **Critical Issue Detection**: Flags forms with zero submissions and major lead capture failures

### OAuth Authentication Enhancement
- Successfully implemented OAuth "Login with HubSpot" authentication
- Fixed scope configuration issues by matching exact HubSpot API requirements
- Configured 9 required scopes: oauth, crm.objects.contacts.read, crm.objects.companies.read, crm.objects.deals.read, crm.objects.listings.read, crm.schemas.listings.read, forms, automation, automation.sequences.read
- Enhanced OAuth setup guide with precise scope requirements
- **Updated to production secure URL**: https://hubspotaudit.replit.app/oauth/callback
- Enhanced access token authentication as prominent fallback option for OAuth issues

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 templates with Flask
- **CSS Framework**: Tailwind CSS for responsive design
- **Icons**: Bootstrap Icons for consistent iconography
- **Static Assets**: Custom CSS for grade color coding and hover effects
- **User Interface**: Clean, professional design with dashboard-style results display

### Backend Architecture
- **Web Framework**: Flask with standard MVC pattern
- **Authentication**: HubSpot OAuth 2.0 integration
- **Session Management**: Flask sessions for token storage
- **Logging**: Python's built-in logging module with DEBUG level
- **PDF Generation**: ReportLab for creating professional audit reports
- **API Integration**: Custom service layer for HubSpot API interactions

## Key Components

### Core Services
1. **HubSpotService** (`hubspot_service.py`): Handles all HubSpot API interactions including OAuth flow and data retrieval
2. **AuditEngine** (`audit_engine.py`): Core business logic for analyzing HubSpot data and generating scores
3. **PDFGenerator** (`pdf_generator.py`): Creates professional PDF reports from audit results

### Web Layer
1. **Application Factory** (`app.py`): Flask app configuration with OAuth settings
2. **Routes** (`routes.py`): Web endpoints for OAuth flow, dashboard, and report generation
3. **Templates**: Responsive HTML templates for user interface

### Audit Categories & Scoring
The system evaluates six key areas with equal weighting (16.7% each):

### Admin & Setup (16.7%)
- **Excellent (5.0)**: 1-10 users, 1-3 super admins, 3+ integrations
- **Good (3.5)**: 11-25 users, 4-5 super admins, 1-2 integrations  
- **Poor (2.0)**: 26+ users, 6+ super admins, 0 integrations

### Properties (16.7%)
- **Excellent (5.0)**: 0-10% unused custom properties
- **Good (3.5)**: 11-25% unused properties
- **Poor (2.0)**: 26%+ unused properties

### Workflows (16.7%)
- **Excellent (5.0)**: 5+ workflows, 0-10% inactive
- **Good (3.5)**: 2-4 workflows, 11-25% inactive
- **Poor (2.0)**: 0-1 workflows, 26%+ inactive

### Forms (16.7%) - Enhanced with Usage Analytics
- **Excellent (5.0)**: 3+ forms, 0-20% unembedded, 0-20% unused (based on 30-day submissions)
- **Good (3.5)**: 1-2 forms, 21-40% unembedded, 21-50% unused forms
- **Poor (2.0)**: 0 forms, 41%+ unembedded, 50%+ unused forms
- **Usage Factors**: Form submission tracking, field consolidation opportunities, lead capture effectiveness

### Reporting (16.7%)
- **Excellent (5.0)**: 2+ dashboards, 1+ custom reports
- **Good (3.5)**: 1 dashboard, 0 custom reports
- **Poor (2.0)**: 0 dashboards, 0 custom reports

### Sales (16.7%)
- **Excellent (5.0)**: 2+ pipelines, 0-5% unassigned deals
- **Good (3.5)**: 1 pipeline, 6-15% unassigned deals
- **Poor (2.0)**: 0 pipelines, 16%+ unassigned deals

## Data Flow

1. **Authentication Flow**: User initiates OAuth → HubSpot authorization → Token exchange → Session storage
2. **Audit Execution**: Token retrieved → API calls to HubSpot → Data analysis → Score calculation
3. **Results Display**: Audit results → Template rendering → Interactive dashboard
4. **Report Export**: Results → PDF generation → File download

## External Dependencies

### HubSpot API Integration
- **OAuth Scopes**: Comprehensive permissions for contacts, companies, deals, workflows, forms, users, and reporting
- **API Endpoints**: Multiple HubSpot REST API endpoints for data collection
- **Rate Limiting**: Built-in handling for API rate limits and error responses

### Third-Party Libraries
- **Flask**: Web framework and routing
- **ReportLab**: PDF generation with custom styling
- **Requests**: HTTP client for API communications
- **Werkzeug**: WSGI utilities and proxy handling

## Deployment Strategy

### Configuration Management
- Environment variables for sensitive data (client secrets, session keys)
- Configurable redirect URIs for different environments
- Debug mode toggle via main.py entry point

### Production Considerations
- ProxyFix middleware for reverse proxy deployments
- Session security with configurable secret keys
- WSGI-compatible application structure
- Host and port configuration for containerized deployments

### Security Features
- OAuth 2.0 for secure HubSpot integration
- Session-based authentication state management
- Environment-based configuration for secrets
- Secure token handling and storage

The application follows a clean separation of concerns with dedicated service layers, comprehensive error handling, and a user-friendly interface designed for marketing operations professionals.