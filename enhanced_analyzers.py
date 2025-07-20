#!/usr/bin/env python3
"""Enhanced analyzers for deeper workflow and property insights"""

import logging
from typing import Dict, List
from hubspot_service import HubSpotService

class WorkflowAnalyzer:
    def __init__(self, hubspot_service: HubSpotService):
        self.hubspot = hubspot_service
    
    def analyze_workflow_triggers(self, workflows: List[Dict]) -> Dict:
        """Analyze common workflow triggers and patterns"""
        try:
            trigger_analysis = {
                'common_triggers': {},
                'object_types': {},
                'trigger_patterns': [],
                'enrollment_data': {}
            }
            
            for workflow in workflows:
                workflow_id = workflow.get('id')
                if not workflow_id:
                    continue
                
                # Get detailed workflow info including triggers
                workflow_details = self._get_workflow_details(workflow_id)
                if not workflow_details:
                    continue
                
                # Analyze triggers
                triggers = workflow_details.get('triggers', [])
                for trigger in triggers:
                    trigger_type = trigger.get('type', 'unknown')
                    object_type = trigger.get('objectType', 'unknown')
                    
                    # Count trigger types
                    if trigger_type not in trigger_analysis['common_triggers']:
                        trigger_analysis['common_triggers'][trigger_type] = 0
                    trigger_analysis['common_triggers'][trigger_type] += 1
                    
                    # Count object types
                    if object_type not in trigger_analysis['object_types']:
                        trigger_analysis['object_types'][object_type] = 0
                    trigger_analysis['object_types'][object_type] += 1
                
                # Get enrollment statistics if available
                enrollment_stats = self._get_workflow_enrollments(workflow_id)
                if enrollment_stats:
                    trigger_analysis['enrollment_data'][workflow_id] = enrollment_stats
            
            # Identify patterns
            trigger_analysis['trigger_patterns'] = self._identify_trigger_patterns(trigger_analysis)
            
            return trigger_analysis
            
        except Exception as e:
            logging.error(f"Workflow trigger analysis error: {str(e)}")
            return {'common_triggers': {}, 'object_types': {}, 'trigger_patterns': [], 'enrollment_data': {}}
    
    def _get_workflow_details(self, workflow_id: str) -> Dict:
        """Get detailed workflow information including triggers"""
        try:
            # Try different API endpoints for workflow details
            endpoints = [
                f'/automation/v3/workflows/{workflow_id}',
                f'/automation/v4/flows/{workflow_id}',
                f'/workflows/v3/workflows/{workflow_id}'
            ]
            
            for endpoint in endpoints:
                data = self.hubspot._make_api_call(endpoint)
                if data:
                    return data
            
            return {}
        except Exception as e:
            logging.debug(f"Error getting workflow details for {workflow_id}: {str(e)}")
            return {}
    
    def _get_workflow_enrollments(self, workflow_id: str) -> Dict:
        """Get workflow enrollment statistics"""
        try:
            endpoint = f'/automation/v3/workflows/{workflow_id}/enrollments'
            data = self.hubspot._make_api_call(endpoint)
            
            if data and 'results' in data:
                enrollments = data['results']
                return {
                    'total_enrollments': len(enrollments),
                    'active_enrollments': len([e for e in enrollments if e.get('status') == 'ENROLLED']),
                    'completed_enrollments': len([e for e in enrollments if e.get('status') == 'COMPLETED'])
                }
            
            return {}
        except Exception as e:
            logging.debug(f"Error getting enrollments for workflow {workflow_id}: {str(e)}")
            return {}
    
    def _identify_trigger_patterns(self, analysis: Dict) -> List[Dict]:
        """Identify common trigger patterns"""
        patterns = []
        
        triggers = analysis.get('common_triggers', {})
        objects = analysis.get('object_types', {})
        
        # Most common trigger types
        if triggers:
            top_trigger = max(triggers.items(), key=lambda x: x[1])
            patterns.append({
                'type': 'common_trigger',
                'description': f"Most workflows use '{top_trigger[0]}' triggers ({top_trigger[1]} workflows)",
                'recommendation': f"Consider standardizing on '{top_trigger[0]}' triggers for consistency"
            })
        
        # Most common object types
        if objects:
            top_object = max(objects.items(), key=lambda x: x[1])
            patterns.append({
                'type': 'common_object',
                'description': f"Most workflows operate on '{top_object[0]}' objects ({top_object[1]} workflows)",
                'recommendation': f"Optimize '{top_object[0]}' object workflows for better performance"
            })
        
        return patterns

class PropertyAnalyzer:
    def __init__(self, hubspot_service: HubSpotService):
        self.hubspot = hubspot_service
    
    def analyze_property_usage(self, properties: List[Dict]) -> Dict:
        """Analyze where and how properties are actually used"""
        try:
            usage_analysis = {
                'form_usage': {},
                'workflow_usage': {},
                'population_stats': {},
                'unused_properties': [],
                'high_value_properties': []
            }
            
            # Analyze property usage in forms
            forms = self.hubspot.get_forms()
            usage_analysis['form_usage'] = self._analyze_form_property_usage(forms, properties)
            
            # Analyze property usage in workflows  
            workflows = self.hubspot.get_workflows()
            usage_analysis['workflow_usage'] = self._analyze_workflow_property_usage(workflows, properties)
            
            # Identify unused properties
            usage_analysis['unused_properties'] = self._identify_unused_properties(
                properties, usage_analysis['form_usage'], usage_analysis['workflow_usage']
            )
            
            # Identify high-value properties (used in multiple places)
            usage_analysis['high_value_properties'] = self._identify_high_value_properties(
                usage_analysis['form_usage'], usage_analysis['workflow_usage']
            )
            
            return usage_analysis
            
        except Exception as e:
            logging.error(f"Property usage analysis error: {str(e)}")
            return {
                'form_usage': {}, 'workflow_usage': {}, 'population_stats': {},
                'unused_properties': [], 'high_value_properties': []
            }
    
    def _analyze_form_property_usage(self, forms: List[Dict], properties: List[Dict]) -> Dict:
        """Analyze which properties are used in forms"""
        form_usage = {}
        
        for form in forms:
            form_name = form.get('name', 'Unknown Form')
            form_fields = []
            
            # Extract field names from form
            field_groups = form.get('formFieldGroups', [])
            for group in field_groups:
                fields = group.get('fields', [])
                for field in fields:
                    field_name = field.get('name')
                    if field_name:
                        form_fields.append(field_name)
                        
                        # Track which forms use each property
                        if field_name not in form_usage:
                            form_usage[field_name] = []
                        form_usage[field_name].append(form_name)
        
        return form_usage
    
    def _analyze_workflow_property_usage(self, workflows: List[Dict], properties: List[Dict]) -> Dict:
        """Analyze which properties are used in workflows"""
        workflow_usage = {}
        
        # This would require detailed workflow analysis
        # For now, return placeholder structure
        for workflow in workflows:
            workflow_name = workflow.get('name', 'Unknown Workflow')
            # TODO: Analyze workflow actions and triggers for property usage
            # This requires detailed workflow API calls
        
        return workflow_usage
    
    def _identify_unused_properties(self, properties: List[Dict], form_usage: Dict, workflow_usage: Dict) -> List[Dict]:
        """Identify properties that aren't used anywhere"""
        unused = []
        
        for prop in properties:
            prop_name = prop.get('name', '')
            if prop_name and prop_name not in form_usage and prop_name not in workflow_usage:
                unused.append({
                    'name': prop_name,
                    'type': prop.get('type', 'unknown'),
                    'object_type': prop.get('objectType', 'unknown')
                })
        
        return unused
    
    def _identify_high_value_properties(self, form_usage: Dict, workflow_usage: Dict) -> List[Dict]:
        """Identify properties used in multiple places (high value)"""
        high_value = []
        
        all_properties = set(list(form_usage.keys()) + list(workflow_usage.keys()))
        
        for prop_name in all_properties:
            form_count = len(form_usage.get(prop_name, []))
            workflow_count = len(workflow_usage.get(prop_name, []))
            total_usage = form_count + workflow_count
            
            if total_usage >= 3:  # Used in 3+ places
                high_value.append({
                    'name': prop_name,
                    'form_usage_count': form_count,
                    'workflow_usage_count': workflow_count,
                    'total_usage': total_usage,
                    'forms_using': form_usage.get(prop_name, []),
                    'workflows_using': workflow_usage.get(prop_name, [])
                })
        
        return sorted(high_value, key=lambda x: x['total_usage'], reverse=True)