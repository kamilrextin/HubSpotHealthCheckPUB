# HubSpot Marketing Operations Audit Tool

## Overview

This is a Flask-based web application that performs comprehensive audits of HubSpot marketing operations. The tool connects to HubSpot via OAuth 2.0 authentication, analyzes various aspects of a HubSpot instance, and provides scored assessments with actionable recommendations. Users can view results in a web dashboard and export detailed PDF reports.

## User Preferences

Preferred communication style: Simple, everyday language.

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

### Audit Categories
The system evaluates six key areas:
- **Admin & Setup**: User management, super admin ratios, integrations
- **Properties**: Usage analysis and optimization recommendations
- **Workflows**: Automation effectiveness and activity levels
- **Forms**: Form utilization and embedding status
- **Reporting**: Dashboard and custom report analysis
- **Sales**: Pipeline setup and deal assignment tracking

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