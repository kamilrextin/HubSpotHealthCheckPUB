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
        self.redirect_uri = os.environ.get("HUBSPOT_REDIRECT_URI", "https://workspace.kamilrextin.replit.app/oauth/callback")
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
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                return response.json()
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
        """Get all workflows"""
        try:
            data = self._make_api_call('/automation/v3/workflows')
            return data.get('results', []) if data else []
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
