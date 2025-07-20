import os
import requests
import logging
from urllib.parse import urlencode
from typing import Dict, List, Optional

class HubSpotService:
    """Service class for HubSpot API interactions"""
    
    def __init__(self, access_token=None):
        self.access_token = access_token
        self.client_id = os.environ.get("HUBSPOT_CLIENT_ID")
        self.client_secret = os.environ.get("HUBSPOT_CLIENT_SECRET")
        # Use environment variable for redirect URI, with fallback to production URL
        self.redirect_uri = os.environ.get("HUBSPOT_REDIRECT_URI", "https://hubspotaudit.replit.app/oauth/callback")
        self.base_url = "https://api.hubapi.com"
        
        # Required scopes for the audit - matching HubSpot app configuration
        self.scopes = [
            'oauth',
            'crm.objects.contacts.read',
            'crm.objects.companies.read', 
            'crm.objects.deals.read',
            'crm.objects.listings.read',
            'crm.schemas.listings.read',
            'forms',
            'automation',
            'automation.sequences.read'
        ]
        
        # Log scope information for debugging
        logging.debug(f"Configured scopes: {', '.join(self.scopes)}")
    
    def get_authorization_url(self) -> str:
        """Generate HubSpot OAuth authorization URL"""
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(self.scopes),
            'response_type': 'code'
        }
        return f"https://app.hubspot.com/oauth/authorize?{urlencode(params)}"
    
    def exchange_code_for_token(self, code: str) -> Optional[Dict]:
        """Exchange authorization code for access token"""
        try:
            data = {
                'grant_type': 'authorization_code',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'redirect_uri': self.redirect_uri,
                'code': code
            }
            
            response = requests.post(
                'https://api.hubapi.com/oauth/v1/token',
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"Token exchange failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logging.error(f"Token exchange error: {str(e)}")
            return None
    
    def _make_api_call(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make authenticated API call to HubSpot"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            url = f"{self.base_url}{endpoint}"
            logging.debug(f"Making API call to: {url}")
            response = requests.get(url, headers=headers, params=params)
            
            logging.debug(f"API Response: {endpoint} - Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if 'results' in data:
                    logging.debug(f"Results found: {len(data['results'])} items")
                elif isinstance(data, list):
                    logging.debug(f"Direct list returned: {len(data)} items")
                else:
                    logging.debug(f"Response structure: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                return data
            else:
                logging.error(f"API call failed: {endpoint} - {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logging.error(f"API call error for {endpoint}: {str(e)}")
            return None
    
    def get_users(self) -> List[Dict]:
        """Get all users from HubSpot"""
        try:
            data = self._make_api_call('/settings/v3/users')
            return data.get('results', []) if data else []
        except Exception as e:
            logging.error(f"Error fetching users: {str(e)}")
            return []
    
    def get_integrations(self) -> List[Dict]:
        """Get active integrations"""
        try:
            data = self._make_api_call('/integrations/v1/me')
            return data.get('results', []) if data else []
        except Exception as e:
            logging.error(f"Error fetching integrations: {str(e)}")
            return []
    
    def get_contact_properties(self) -> List[Dict]:
        """Get all contact properties"""
        try:
            data = self._make_api_call('/crm/v3/properties/contacts')
            return data.get('results', []) if data else []
        except Exception as e:
            logging.error(f"Error fetching contact properties: {str(e)}")
            return []
    
    def get_company_properties(self) -> List[Dict]:
        """Get all company properties"""
        try:
            data = self._make_api_call('/crm/v3/properties/companies')
            return data.get('results', []) if data else []
        except Exception as e:
            logging.error(f"Error fetching company properties: {str(e)}")
            return []
    
    def get_deal_properties(self) -> List[Dict]:
        """Get all deal properties"""
        try:
            data = self._make_api_call('/crm/v3/properties/deals')
            return data.get('results', []) if data else []
        except Exception as e:
            logging.error(f"Error fetching deal properties: {str(e)}")
            return []
    
    def get_workflows(self) -> List[Dict]:
        """Get all workflows - try multiple API endpoints"""
        try:
            # Try multiple endpoints since HubSpot workflow APIs vary
            endpoints_to_try = [
                '/automation/v3/workflows',  # Standard workflows API
                '/automation/v4/flows',      # Newer flows API  
                '/workflows/v3/workflows',   # Alternative endpoint
                '/automation/v2/workflows'   # Legacy fallback
            ]
            
            for endpoint in endpoints_to_try:
                logging.debug(f"Trying workflows endpoint: {endpoint}")
                data = self._make_api_call(endpoint)
                
                if data:
                    if 'results' in data and data['results']:
                        logging.debug(f"Workflows found via {endpoint}: {len(data['results'])}")
                        return data['results']
                    elif isinstance(data, list) and data:
                        logging.debug(f"Workflows found as direct list via {endpoint}: {len(data)}")
                        return data
                    elif 'workflows' in data and data['workflows']:
                        logging.debug(f"Workflows found in 'workflows' key via {endpoint}: {len(data['workflows'])}")
                        return data['workflows']
            
            logging.warning("No workflows found in any API endpoint")
            return []
            
        except Exception as e:
            logging.error(f"Error fetching workflows: {str(e)}")
            return []
    
    def get_forms(self) -> List[Dict]:
        """Get all forms"""
        try:
            data = self._make_api_call('/forms/v2/forms')
            return data if data else []
        except Exception as e:
            logging.error(f"Error fetching forms: {str(e)}")
            return []
    
    def get_form_submissions(self, form_id: str, days_back: int = 30) -> Dict:
        """Get form submission statistics for a specific form"""
        try:
            # Get submissions for the last X days
            import datetime
            end_date = datetime.datetime.now()
            start_date = end_date - datetime.timedelta(days=days_back)
            
            params = {
                'formId': form_id,
                'after': int(start_date.timestamp() * 1000),  # HubSpot uses milliseconds
                'before': int(end_date.timestamp() * 1000)
            }
            
            data = self._make_api_call('/form-integrations/v1/submissions/forms', params)
            return {
                'submissions_count': len(data.get('results', [])) if data else 0,
                'form_id': form_id,
                'period_days': days_back
            }
        except Exception as e:
            logging.debug(f"Error fetching form submissions for {form_id}: {str(e)}")
            return {'submissions_count': 0, 'form_id': form_id, 'period_days': days_back}
    
    def analyze_form_field_usage(self, forms: List[Dict]) -> Dict:
        """Analyze which fields are commonly used across forms"""
        try:
            field_usage = {}
            total_forms = len(forms)
            
            for form in forms:
                form_fields = form.get('formFieldGroups', [])
                for field_group in form_fields:
                    fields = field_group.get('fields', [])
                    for field in fields:
                        field_name = field.get('name', '')
                        field_type = field.get('fieldType', '')
                        
                        if field_name and field_type:
                            key = f"{field_name}_{field_type}"
                            if key not in field_usage:
                                field_usage[key] = {
                                    'name': field_name,
                                    'type': field_type,
                                    'forms_using': [],
                                    'usage_count': 0
                                }
                            
                            field_usage[key]['forms_using'].append(form.get('name', 'Unknown'))
                            field_usage[key]['usage_count'] += 1
            
            # Calculate usage percentages and find common fields
            common_fields = []
            for field_key, field_data in field_usage.items():
                usage_percentage = (field_data['usage_count'] / total_forms * 100) if total_forms > 0 else 0
                field_data['usage_percentage'] = round(usage_percentage, 1)
                
                # Fields used in 50%+ of forms could indicate consolidation opportunities
                if usage_percentage >= 50 and field_data['usage_count'] > 1:
                    common_fields.append(field_data)
            
            return {
                'total_unique_fields': len(field_usage),
                'common_fields': common_fields,
                'field_usage_details': field_usage
            }
            
        except Exception as e:
            logging.error(f"Error analyzing form field usage: {str(e)}")
            return {'total_unique_fields': 0, 'common_fields': [], 'field_usage_details': {}}
    
    def get_dashboards(self) -> List[Dict]:
        """Get all dashboards"""
        try:
            data = self._make_api_call('/reports/v2/dashboards')
            return data.get('results', []) if data else []
        except Exception as e:
            logging.error(f"Error fetching dashboards: {str(e)}")
            return []
    
    def get_reports(self) -> List[Dict]:
        """Get all reports"""
        try:
            data = self._make_api_call('/reports/v2/reports')
            return data.get('results', []) if data else []
        except Exception as e:
            logging.error(f"Error fetching reports: {str(e)}")
            return []
    
    def get_pipelines(self) -> List[Dict]:
        """Get all deal pipelines"""
        try:
            data = self._make_api_call('/crm/v3/pipelines/deals')
            return data.get('results', []) if data else []
        except Exception as e:
            logging.error(f"Error fetching pipelines: {str(e)}")
            return []
    
    def get_contact_count_by_property(self, property_name: str) -> int:
        """Get count of contacts that have a specific property populated"""
        try:
            params = {
                'properties': property_name,
                'limit': 1
            }
            data = self._make_api_call('/crm/v3/objects/contacts', params)
            return data.get('total', 0) if data else 0
        except Exception as e:
            logging.error(f"Error getting contact count for property {property_name}: {str(e)}")
            return 0
