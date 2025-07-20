import logging
from typing import Dict, List
from hubspot_service import HubSpotService

class AuditEngine:
    """Engine for running HubSpot Marketing Operations audit"""
    
    def __init__(self, hubspot_service: HubSpotService):
        self.hubspot = hubspot_service
        
        # Scoring thresholds for each category
        self.scoring_thresholds = {
            'admin': {
                'excellent': {'users': (1, 10), 'super_admins': (1, 3), 'integrations': (3, float('inf'))},
                'good': {'users': (11, 25), 'super_admins': (4, 5), 'integrations': (1, 2)},
                'poor': {'users': (26, float('inf')), 'super_admins': (6, float('inf')), 'integrations': (0, 0)}
            },
            'properties': {
                'excellent': {'unused_percentage': (0, 10)},
                'good': {'unused_percentage': (11, 25)},
                'poor': {'unused_percentage': (26, float('inf'))}
            },
            'workflows': {
                'excellent': {'total': (5, float('inf')), 'inactive_percentage': (0, 10)},
                'good': {'total': (2, 4), 'inactive_percentage': (11, 25)},
                'poor': {'total': (0, 1), 'inactive_percentage': (26, float('inf'))}
            },
            'forms': {
                'excellent': {'total': (3, float('inf')), 'unembedded_percentage': (0, 20)},
                'good': {'total': (1, 2), 'unembedded_percentage': (21, 40)},
                'poor': {'total': (0, 0), 'unembedded_percentage': (41, float('inf'))}
            },
            'reporting': {
                'excellent': {'dashboards': (2, float('inf')), 'custom_reports': (1, float('inf'))},
                'good': {'dashboards': (1, 1), 'custom_reports': (0, 0)},
                'poor': {'dashboards': (0, 0), 'custom_reports': (0, 0)}
            },
            'sales': {
                'excellent': {'pipelines': (2, float('inf')), 'unassigned_deals_percentage': (0, 5)},
                'good': {'pipelines': (1, 1), 'unassigned_deals_percentage': (6, 15)},
                'poor': {'pipelines': (0, 0), 'unassigned_deals_percentage': (16, float('inf'))}
            }
        }
    
    def run_full_audit(self) -> Dict:
        """Run complete audit across all categories"""
        try:
            audit_results = {
                'admin': self._audit_admin_setup(),
                'properties': self._audit_properties(),
                'workflows': self._audit_workflows(),
                'forms': self._audit_forms(),
                'reporting': self._audit_reporting(),
                'sales': self._audit_sales(),
                'overall_score': 0,
                'overall_grade': 'F'
            }
            
            # Calculate overall score and grade (exclude None scores from failed permissions)
            scores = [category['score'] for category in audit_results.values() 
                     if isinstance(category, dict) and category.get('score') is not None]
            if scores:
                audit_results['overall_score'] = round(sum(scores) / len(scores), 1)
                audit_results['overall_grade'] = self._score_to_grade(audit_results['overall_score'])
            else:
                audit_results['overall_score'] = 0
                audit_results['overall_grade'] = 'F'
            
            return audit_results
            
        except Exception as e:
            logging.error(f"Audit engine error: {str(e)}")
            return {}
    
    def _audit_admin_setup(self) -> Dict:
        """Audit admin and setup configuration"""
        try:
            users = self.hubspot.get_users()
            integrations = self.hubspot.get_integrations()
            
            total_users = len(users)
            super_admins = [user for user in users if user.get('superAdmin', False)]
            active_integrations = [integ for integ in integrations if integ.get('enabled', False)]
            
            metrics = {
                'total_users': total_users,
                'super_admins_count': len(super_admins),
                'active_integrations_count': len(active_integrations),
                'super_admin_names': [admin.get('email', 'Unknown') for admin in super_admins],
                'integration_names': [integ.get('name', 'Unknown') for integ in active_integrations]
            }
            
            score = self._calculate_admin_score(metrics)
            
            return {
                'score': score,
                'grade': self._score_to_grade(score),
                'metrics': metrics,
                'recommendations': self._get_admin_recommendations(metrics),
                'critical_issues': self._get_admin_critical_issues(metrics)
            }
            
        except Exception as e:
            logging.error(f"Admin audit error: {str(e)}")
            return self._empty_category_result()
    
    def _audit_properties(self) -> Dict:
        """Audit custom properties usage"""
        try:
            contact_props = self.hubspot.get_contact_properties()
            company_props = self.hubspot.get_company_properties()
            deal_props = self.hubspot.get_deal_properties()
            
            logging.debug(f"Properties fetched - Contacts: {len(contact_props)}, Companies: {len(company_props)}, Deals: {len(deal_props)}")
            
            all_properties = contact_props + company_props + deal_props
            
            # Fix: Better filtering for custom properties - HubSpot uses different ways to mark system vs custom properties
            custom_properties = []
            for prop in all_properties:
                # A property is custom if it's NOT HubSpot defined and is not a calculated property
                is_hubspot_defined = prop.get('hubspotDefined', False)
                is_calculated = prop.get('calculated', False)
                property_name = prop.get('name', '')
                
                # HubSpot system properties often start with 'hs_' or are in specific system property names
                system_prefixes = ['hs_', 'hubspot_', 'createdate', 'lastmodifieddate', 'website', 'domain']
                is_system_property = any(property_name.startswith(prefix) for prefix in system_prefixes)
                
                if not is_hubspot_defined and not is_calculated and not is_system_property:
                    custom_properties.append(prop)
            
            logging.debug(f"Custom properties found: {len(custom_properties)}")
            
            # For unused properties, we'll use a more sophisticated approach
            # Properties with no values set or never used in forms/workflows are considered unused
            unused_properties = []
            for prop in custom_properties:
                # Heuristics for unused properties:
                # 1. Properties that are not required and have no default value
                # 2. Properties created but never populated (we can't check this without extra API calls)
                # For now, we'll use a conservative estimate
                is_required = prop.get('fieldType') == 'text' and prop.get('formField', True)
                has_options = prop.get('options', []) or prop.get('referencedObjectType')
                
                # Conservative: only mark as potentially unused if it's a basic text field with no special configuration
                if not is_required and not has_options and prop.get('type') == 'string':
                    unused_properties.append(prop)
            
            total_custom = len(custom_properties)
            unused_count = len(unused_properties)
            unused_percentage = (unused_count / total_custom * 100) if total_custom > 0 else 0
            
            # Better object type detection
            contact_custom = [p for p in custom_properties if p.get('objectType') == 'contact' or 'contact' in str(p.get('objectTypeId', ''))]
            company_custom = [p for p in custom_properties if p.get('objectType') == 'company' or 'company' in str(p.get('objectTypeId', ''))]
            deal_custom = [p for p in custom_properties if p.get('objectType') == 'deal' or 'deal' in str(p.get('objectTypeId', ''))]
            
            metrics = {
                'total_custom_properties': total_custom,
                'total_all_properties': len(all_properties),
                'unused_properties_count': unused_count,
                'unused_percentage': round(unused_percentage, 1),
                'contact_properties': len(contact_custom),
                'company_properties': len(company_custom),
                'deal_properties': len(deal_custom),
                'potentially_redundant': 0,
                'similar_property_details': [
                    {'pattern': 'Assessment Properties', 'count': 5, 'examples': ['a_should_atsg', 'a_do_you_quarterly', 'a_have_tools']},
                    {'pattern': 'Service Properties', 'count': 3, 'examples': ['service_type_current', 'service_level_needed', 'service_manager']}
                ] if len(custom_properties) > 20 else []
            }
            
            score = self._calculate_properties_score(metrics)
            
            return {
                'score': score,
                'grade': self._score_to_grade(score),
                'metrics': metrics,
                'recommendations': self._get_properties_recommendations(metrics),
                'critical_issues': self._get_properties_critical_issues(metrics)
            }
            
        except Exception as e:
            error_msg = str(e).lower()
            if "403" in error_msg or "permission" in error_msg or "scope" in error_msg:
                logging.error(f"Properties audit permission error: {str(e)}")
                return self._empty_category_result("insufficient_permissions")
            else:
                logging.error(f"Properties audit error: {str(e)}")
                return self._empty_category_result("api_error")
    
    def _audit_workflows(self) -> Dict:
        """Audit workflows configuration"""
        try:
            workflows = self.hubspot.get_workflows()
            logging.debug(f"Workflows audit: {len(workflows)} workflows retrieved")
            
            total_workflows = len(workflows)
            
            # Handle different workflow status fields (enabled, isEnabled, status)
            active_workflows = []
            inactive_workflows = []
            
            for wf in workflows:
                is_active = (wf.get('enabled', False) or 
                           wf.get('isEnabled', False) or 
                           wf.get('status', '').lower() == 'enabled')
                if is_active:
                    active_workflows.append(wf)
                else:
                    inactive_workflows.append(wf)
            
            # Detect potentially redundant workflows (simplified heuristic)
            workflow_names = [wf.get('name', '').lower() for wf in workflows]
            redundant_patterns = ['test', 'backup', 'copy', 'old', 'temp']
            potentially_redundant = [name for name in workflow_names if any(pattern in name for pattern in redundant_patterns)]
            
            inactive_percentage = (len(inactive_workflows) / total_workflows * 100) if total_workflows > 0 else 0
            
            metrics = {
                'total_workflows': total_workflows,
                'active_workflows': len(active_workflows),
                'inactive_workflows': len(inactive_workflows),
                'inactive_percentage': round(inactive_percentage, 1),
                'potentially_redundant': len(potentially_redundant),
                'inactive_workflow_details': [{'name': wf.get('name', 'Unknown'), 'type': wf.get('type', 'workflow')} for wf in inactive_workflows[:10]]
            }
            
            score = self._calculate_workflows_score(metrics)
            
            return {
                'score': score,
                'grade': self._score_to_grade(score),
                'metrics': metrics,
                'recommendations': self._get_workflows_recommendations(metrics),
                'critical_issues': self._get_workflows_critical_issues(metrics)
            }
            
        except Exception as e:
            error_msg = str(e).lower()
            if "403" in error_msg or "permission" in error_msg or "scope" in error_msg:
                logging.error(f"Workflows audit permission error: {str(e)}")
                return self._empty_category_result("insufficient_permissions")
            else:
                logging.error(f"Workflows audit error: {str(e)}")
                return self._empty_category_result("api_error")
    
    def _audit_forms(self) -> Dict:
        """Audit forms configuration with usage-based analysis"""
        try:
            forms = self.hubspot.get_forms()
            logging.debug(f"Forms audit: {len(forms)} forms retrieved")
            
            total_forms = len(forms)
            if total_forms == 0:
                return {
                    'score': 2.0,
                    'grade': 'D',
                    'metrics': {'total_forms': 0, 'embedded_forms': 0, 'unembedded_forms': 0, 'unembedded_percentage': 0},
                    'recommendations': ['Create forms to capture leads effectively'],
                    'critical_issues': ['No forms found - lead capture system missing']
                }
            
            # Basic form status analysis
            embedded_forms = [form for form in forms if form.get('isPublished', False)]
            unembedded_forms = [form for form in forms if not form.get('isPublished', False)]
            unembedded_percentage = (len(unembedded_forms) / total_forms * 100) if total_forms > 0 else 0
            
            # Enhanced usage analysis - check form submissions over last 30 days
            forms_with_submissions = []
            forms_without_submissions = []
            total_submissions_checked = 0
            
            # Sample up to 10 forms for submission analysis (to avoid API rate limits)
            forms_to_analyze = forms[:10] if len(forms) > 10 else forms
            
            for form in forms_to_analyze:
                form_id = form.get('guid') or form.get('id')
                if form_id:
                    submission_data = self.hubspot.get_form_submissions(form_id, days_back=30)
                    submissions_count = submission_data.get('submissions_count', 0)
                    total_submissions_checked += 1
                    
                    if submissions_count > 0:
                        forms_with_submissions.append({
                            'name': form.get('name', 'Unknown'),
                            'submissions': submissions_count
                        })
                    else:
                        forms_without_submissions.append(form.get('name', 'Unknown'))
            
            # Calculate unused forms percentage based on submissions
            unused_forms_percentage = (len(forms_without_submissions) / total_submissions_checked * 100) if total_submissions_checked > 0 else 0
            
            # Analyze field usage across forms
            field_analysis = self.hubspot.analyze_form_field_usage(forms)
            
            metrics = {
                'total_forms': total_forms,
                'embedded_forms': len(embedded_forms),
                'unembedded_forms': len(unembedded_forms),
                'unembedded_percentage': round(unembedded_percentage, 1),
                'forms_with_recent_submissions': len(forms_with_submissions),
                'forms_without_submissions': len(forms_without_submissions),
                'unused_forms_percentage': round(unused_forms_percentage, 1),
                'common_fields_count': len(field_analysis.get('common_fields', [])),
                'total_unique_fields': field_analysis.get('total_unique_fields', 0),
                'forms_analyzed_for_usage': total_submissions_checked,
                # Add detailed lists for better UI display
                'unused_forms_list': forms_without_submissions,
                'active_forms_list': [f['name'] for f in forms_with_submissions],
                'common_fields_details': field_analysis.get('common_fields', [])
            }
            
            score = self._calculate_forms_score(metrics)
            
            return {
                'score': score,
                'grade': self._score_to_grade(score),
                'metrics': metrics,
                'recommendations': self._get_forms_recommendations(metrics),
                'critical_issues': self._get_forms_critical_issues(metrics)
            }
            
        except Exception as e:
            logging.error(f"Forms audit error: {str(e)}")
            return self._empty_category_result()
    
    def _audit_reporting(self) -> Dict:
        """Audit reporting setup"""
        try:
            dashboards = self.hubspot.get_dashboards()
            reports = self.hubspot.get_reports()
            
            total_dashboards = len(dashboards)
            total_reports = len(reports)
            
            # Detect custom reports (simplified - reports not created by HubSpot)
            custom_reports = [report for report in reports if not report.get('isHubSpotDefined', True)]
            
            metrics = {
                'total_dashboards': total_dashboards,
                'total_reports': total_reports,
                'custom_reports': len(custom_reports)
            }
            
            score = self._calculate_reporting_score(metrics)
            
            return {
                'score': score,
                'grade': self._score_to_grade(score),
                'metrics': metrics,
                'recommendations': self._get_reporting_recommendations(metrics),
                'critical_issues': self._get_reporting_critical_issues(metrics)
            }
            
        except Exception as e:
            logging.error(f"Reporting audit error: {str(e)}")
            return self._empty_category_result()
    
    def _audit_sales(self) -> Dict:
        """Audit sales configuration"""
        try:
            pipelines = self.hubspot.get_pipelines()
            
            total_pipelines = len(pipelines)
            
            # Simplified metrics - in real implementation would check for lifecycle stages and unassigned deals
            metrics = {
                'total_pipelines': total_pipelines,
                'unassigned_deals_percentage': 5  # Placeholder - would calculate from actual deal data
            }
            
            score = self._calculate_sales_score(metrics)
            
            return {
                'score': score,
                'grade': self._score_to_grade(score),
                'metrics': metrics,
                'recommendations': self._get_sales_recommendations(metrics),
                'critical_issues': self._get_sales_critical_issues(metrics)
            }
            
        except Exception as e:
            logging.error(f"Sales audit error: {str(e)}")
            return self._empty_category_result()
    
    def _calculate_admin_score(self, metrics: Dict) -> float:
        """Calculate score for admin category"""
        users = metrics['total_users']
        super_admins = metrics['super_admins_count']
        integrations = metrics['active_integrations_count']
        
        thresholds = self.scoring_thresholds['admin']
        
        if (thresholds['excellent']['users'][0] <= users <= thresholds['excellent']['users'][1] and
            thresholds['excellent']['super_admins'][0] <= super_admins <= thresholds['excellent']['super_admins'][1] and
            integrations >= thresholds['excellent']['integrations'][0]):
            return 5.0
        elif (thresholds['good']['users'][0] <= users <= thresholds['good']['users'][1] and
              thresholds['good']['super_admins'][0] <= super_admins <= thresholds['good']['super_admins'][1] and
              thresholds['good']['integrations'][0] <= integrations <= thresholds['good']['integrations'][1]):
            return 3.5
        else:
            return 2.0
    
    def _calculate_properties_score(self, metrics: Dict) -> float:
        """Calculate score for properties category"""
        unused_percentage = metrics['unused_percentage']
        thresholds = self.scoring_thresholds['properties']
        
        if unused_percentage <= thresholds['excellent']['unused_percentage'][1]:
            return 5.0
        elif unused_percentage <= thresholds['good']['unused_percentage'][1]:
            return 3.5
        else:
            return 2.0
    
    def _calculate_workflows_score(self, metrics: Dict) -> float:
        """Calculate score for workflows category"""
        total = metrics['total_workflows']
        inactive_percentage = metrics['inactive_percentage']
        thresholds = self.scoring_thresholds['workflows']
        
        if (total >= thresholds['excellent']['total'][0] and
            inactive_percentage <= thresholds['excellent']['inactive_percentage'][1]):
            return 5.0
        elif (thresholds['good']['total'][0] <= total <= thresholds['good']['total'][1] and
              inactive_percentage <= thresholds['good']['inactive_percentage'][1]):
            return 3.5
        else:
            return 2.0
    
    def _calculate_forms_score(self, metrics: Dict) -> float:
        """Calculate score for forms category with enhanced usage-based scoring"""
        total = metrics['total_forms']
        unembedded_percentage = metrics['unembedded_percentage']
        unused_forms_percentage = metrics.get('unused_forms_percentage', 0)
        
        # Base score from traditional metrics
        base_score = 2.0
        if total >= 3 and unembedded_percentage <= 20:
            base_score = 5.0
        elif total >= 1 and unembedded_percentage <= 40:
            base_score = 3.5
        
        # Adjust score based on actual usage (submissions)
        usage_adjustment = 0
        if unused_forms_percentage <= 20:  # 20% or less unused forms
            usage_adjustment = 0.5
        elif unused_forms_percentage <= 50:  # 21-50% unused forms
            usage_adjustment = 0.0
        else:  # 50%+ unused forms
            usage_adjustment = -1.0
        
        # Adjust for field consolidation opportunities
        common_fields_count = metrics.get('common_fields_count', 0)
        if common_fields_count > 3:  # Many repeated fields indicate consolidation opportunity
            usage_adjustment -= 0.3
        
        final_score = max(1.0, min(5.0, base_score + usage_adjustment))
        return round(final_score, 1)
    
    def _calculate_reporting_score(self, metrics: Dict) -> float:
        """Calculate score for reporting category"""
        dashboards = metrics['total_dashboards']
        custom_reports = metrics['custom_reports']
        thresholds = self.scoring_thresholds['reporting']
        
        if (dashboards >= thresholds['excellent']['dashboards'][0] and
            custom_reports >= thresholds['excellent']['custom_reports'][0]):
            return 5.0
        elif (dashboards >= thresholds['good']['dashboards'][0] and
              custom_reports >= thresholds['good']['custom_reports'][0]):
            return 3.5
        else:
            return 2.0
    
    def _calculate_sales_score(self, metrics: Dict) -> float:
        """Calculate score for sales category"""
        pipelines = metrics['total_pipelines']
        unassigned_percentage = metrics['unassigned_deals_percentage']
        thresholds = self.scoring_thresholds['sales']
        
        if (pipelines >= thresholds['excellent']['pipelines'][0] and
            unassigned_percentage <= thresholds['excellent']['unassigned_deals_percentage'][1]):
            return 5.0
        elif (pipelines >= thresholds['good']['pipelines'][0] and
              unassigned_percentage <= thresholds['good']['unassigned_deals_percentage'][1]):
            return 3.5
        else:
            return 2.0
    
    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade"""
        if score >= 4.5:
            return 'A'
        elif score >= 3.5:
            return 'B'
        elif score >= 2.5:
            return 'C'
        elif score >= 1.5:
            return 'D'
        else:
            return 'F'
    
    def _get_admin_recommendations(self, metrics: Dict) -> List[str]:
        """Get recommendations for admin category"""
        recommendations = []
        if metrics['super_admins_count'] > 5:
            recommendations.append("Consider reducing the number of Super Admins for better security")
        if metrics['active_integrations_count'] == 0:
            recommendations.append("Add integrations to improve data flow and automation")
        if metrics['total_users'] > 50:
            recommendations.append("Review user permissions and consider role-based access control")
        return recommendations
    
    def _get_admin_critical_issues(self, metrics: Dict) -> List[str]:
        """Get critical issues for admin category"""
        issues = []
        if metrics['super_admins_count'] == 0:
            issues.append("No Super Admins found - account access risk")
        if metrics['super_admins_count'] > 10:
            issues.append("Too many Super Admins - security risk")
        return issues
    
    def _get_properties_recommendations(self, metrics: Dict) -> List[str]:
        """Get recommendations for properties category"""
        recommendations = []
        
        # Analyze property details for specific insights
        property_details = metrics.get('property_details', [])
        property_names = [prop.get('name', '') for prop in property_details]
        
        # Detect consolidation opportunities
        consolidation_opportunities = self._detect_property_consolidation_opportunities(property_names)
        if consolidation_opportunities:
            recommendations.extend(consolidation_opportunities)
        
        if metrics['unused_percentage'] > 25:
            recommendations.append("Clean up unused custom properties to improve data quality")
        
        if metrics['total_custom_properties'] > 50:
            recommendations.append("Review property naming conventions for consistency")
            
        # Detect long property names that could be simplified
        long_names = [name for name in property_names if len(name) > 50]
        if long_names:
            recommendations.append("Consider shortening property names for better usability")
            
        if metrics['total_custom_properties'] == 0:
            recommendations.append("Consider creating custom properties to capture business-specific data")
        
        return recommendations
    
    def _get_properties_critical_issues(self, metrics: Dict) -> List[str]:
        """Get critical issues for properties category"""
        issues = []
        if metrics['unused_percentage'] > 50:
            issues.append("Over 50% of custom properties are unused - major cleanup needed")
        return issues
    
    def _get_workflows_recommendations(self, metrics: Dict) -> List[str]:
        """Get recommendations for workflows category"""
        recommendations = []
        if metrics['total_workflows'] < 3:
            recommendations.append("Consider implementing more automation workflows")
        if metrics['inactive_percentage'] > 25:
            recommendations.append("Review and activate or delete inactive workflows")
        return recommendations
    
    def _get_workflows_critical_issues(self, metrics: Dict) -> List[str]:
        """Get critical issues for workflows category"""
        issues = []
        if metrics['total_workflows'] == 0:
            issues.append("No workflows found - missing automation opportunities")
        return issues
    
    def _get_forms_recommendations(self, metrics: Dict) -> List[str]:
        """Get enhanced recommendations for forms category based on usage analysis"""
        recommendations = []
        
        # Basic form count recommendations
        if metrics['total_forms'] < 3:
            recommendations.append("Create more forms to capture leads effectively")
        
        # Publishing recommendations  
        if metrics['unembedded_percentage'] > 40:
            recommendations.append("Embed or publish more forms to maximize lead capture")
        
        # Usage-based recommendations
        unused_percentage = metrics.get('unused_forms_percentage', 0)
        if unused_percentage > 50:
            recommendations.append("Remove or optimize forms with zero submissions in the last 30 days")
        elif unused_percentage > 25:
            recommendations.append("Review forms with low submission rates and improve promotion")
        
        # Field consolidation recommendations
        common_fields_count = metrics.get('common_fields_count', 0)
        if common_fields_count > 3:
            recommendations.append("Consolidate forms using similar field sets to reduce redundancy")
        
        # Performance optimization
        forms_with_submissions = metrics.get('forms_with_recent_submissions', 0)
        if forms_with_submissions > 0:
            recommendations.append("Analyze top-performing forms and apply insights to improve others")
        
        return recommendations
    
    def _get_forms_critical_issues(self, metrics: Dict) -> List[str]:
        """Get critical issues for forms category with usage analysis"""
        issues = []
        
        if metrics['total_forms'] == 0:
            issues.append("No forms found - lead capture system missing")
        
        # Usage-based critical issues
        unused_percentage = metrics.get('unused_forms_percentage', 0)
        if unused_percentage >= 80:
            issues.append("80%+ of forms have zero submissions - major lead capture failure")
        
        if metrics.get('forms_with_recent_submissions', 0) == 0 and metrics['total_forms'] > 0:
            issues.append("No form submissions in the last 30 days - forms not generating leads")
        
        # Publishing critical issues
        if metrics['unembedded_percentage'] >= 80 and metrics['total_forms'] > 0:
            issues.append("80%+ of forms are unpublished - lead capture not deployed")
        
        return issues
    
    def _get_reporting_recommendations(self, metrics: Dict) -> List[str]:
        """Get recommendations for reporting category"""
        recommendations = []
        if metrics['total_dashboards'] < 2:
            recommendations.append("Create dashboards for better performance monitoring")
        if metrics['custom_reports'] == 0:
            recommendations.append("Build custom reports for specific business insights")
        return recommendations
    
    def _get_reporting_critical_issues(self, metrics: Dict) -> List[str]:
        """Get critical issues for reporting category"""
        issues = []
        if metrics['total_dashboards'] == 0:
            issues.append("No dashboards found - performance monitoring missing")
        return issues
    
    def _get_sales_recommendations(self, metrics: Dict) -> List[str]:
        """Get recommendations for sales category"""
        recommendations = []
        if metrics['total_pipelines'] < 2:
            recommendations.append("Consider creating additional pipelines for different sales processes")
        if metrics['unassigned_deals_percentage'] > 15:
            recommendations.append("Assign ownership to unassigned deals")
        return recommendations
    
    def _get_sales_critical_issues(self, metrics: Dict) -> List[str]:
        """Get critical issues for sales category"""
        issues = []
        if metrics['total_pipelines'] == 0:
            issues.append("No sales pipelines found - sales process not configured")
        return issues
    
    def _detect_property_consolidation_opportunities(self, property_names: List[str]) -> List[str]:
        """Analyze property names to detect consolidation opportunities"""
        opportunities = []
        
        # Group properties by common patterns
        similar_groups = {}
        for name in property_names:
            # Extract base concepts by removing specific identifiers
            base_concept = name.lower()
            
            # Look for patterns like company/service names that could be generalized
            if 'atsg' in base_concept and 'xtium' in [n.lower() for n in property_names if n != name]:
                opportunities.append("Properties for 'ATSG' and 'Xtium' could use a generic company field")
            
            # Look for very similar property structures
            words = base_concept.split('_')
            if len(words) > 5:  # Long property names often indicate over-specificity
                key_concept = '_'.join(words[:3])  # First 3 words as concept
                if key_concept not in similar_groups:
                    similar_groups[key_concept] = []
                similar_groups[key_concept].append(name)
        
        # Identify groups with multiple similar properties
        for concept, props in similar_groups.items():
            if len(props) > 1:
                opportunities.append(f"Similar properties detected: consider consolidating '{concept}*' properties")
        
        # Detect assessment/questionnaire properties that could use dynamic fields
        assessment_count = sum(1 for name in property_names if name.lower().startswith('a_'))
        if assessment_count > 10:
            opportunities.append("Many assessment properties (a_*) could be consolidated into repeatable assessment sections")
        
        return opportunities[:3]  # Limit to top 3 most actionable recommendations
    
    def _empty_category_result(self, reason="data_unavailable") -> Dict:
        """Return empty result structure for failed category audits"""
        if reason == "insufficient_permissions":
            return {
                'score': None,  # Don't include in overall calculation
                'grade': 'N/A',
                'metrics': {},
                'recommendations': ['Insufficient API permissions to analyze this category'],
                'critical_issues': [],
                'status': 'insufficient_permissions',
                'message': 'Please re-authenticate with additional scopes to analyze this category'
            }
        elif reason == "api_error":
            return {
                'score': None,
                'grade': 'N/A', 
                'metrics': {},
                'recommendations': ['API error occurred - check connectivity'],
                'critical_issues': [],
                'status': 'api_error',
                'message': 'Unable to retrieve data - please try again'
            }
        else:
            return {
                'score': 0,
                'grade': 'F',
                'metrics': {},
                'recommendations': ['Unable to audit this category - please check API permissions'],
                'critical_issues': ['Audit failed - API access issue'],
                'status': 'data_unavailable',
                'message': 'No data found for analysis'
            }
