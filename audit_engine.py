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
            
            # Calculate overall score and grade
            scores = [category['score'] for category in audit_results.values() if isinstance(category, dict) and 'score' in category]
            if scores:
                audit_results['overall_score'] = round(sum(scores) / len(scores), 1)
                audit_results['overall_grade'] = self._score_to_grade(audit_results['overall_score'])
            
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
            
            all_properties = contact_props + company_props + deal_props
            custom_properties = [prop for prop in all_properties if not prop.get('hubspotDefined', True)]
            
            # Check usage for custom properties (simplified - in real implementation would check actual usage)
            unused_properties = []
            for prop in custom_properties:
                # This is a simplified check - real implementation would query objects with the property
                if prop.get('calculated', False) or not prop.get('hasUniqueValue', True):
                    unused_properties.append(prop)
            
            total_custom = len(custom_properties)
            unused_count = len(unused_properties)
            unused_percentage = (unused_count / total_custom * 100) if total_custom > 0 else 0
            
            metrics = {
                'total_custom_properties': total_custom,
                'unused_properties_count': unused_count,
                'unused_percentage': round(unused_percentage, 1),
                'contact_properties': len([p for p in custom_properties if 'contact' in p.get('objectType', '')]),
                'company_properties': len([p for p in custom_properties if 'company' in p.get('objectType', '')]),
                'deal_properties': len([p for p in custom_properties if 'deal' in p.get('objectType', '')])
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
            logging.error(f"Properties audit error: {str(e)}")
            return self._empty_category_result()
    
    def _audit_workflows(self) -> Dict:
        """Audit workflows configuration"""
        try:
            workflows = self.hubspot.get_workflows()
            
            total_workflows = len(workflows)
            active_workflows = [wf for wf in workflows if wf.get('enabled', False)]
            inactive_workflows = [wf for wf in workflows if not wf.get('enabled', False)]
            
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
                'potentially_redundant': len(potentially_redundant)
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
            logging.error(f"Workflows audit error: {str(e)}")
            return self._empty_category_result()
    
    def _audit_forms(self) -> Dict:
        """Audit forms configuration"""
        try:
            forms = self.hubspot.get_forms()
            
            total_forms = len(forms)
            embedded_forms = [form for form in forms if form.get('isPublished', False)]
            unembedded_forms = [form for form in forms if not form.get('isPublished', False)]
            
            unembedded_percentage = (len(unembedded_forms) / total_forms * 100) if total_forms > 0 else 0
            
            metrics = {
                'total_forms': total_forms,
                'embedded_forms': len(embedded_forms),
                'unembedded_forms': len(unembedded_forms),
                'unembedded_percentage': round(unembedded_percentage, 1)
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
        """Calculate score for forms category"""
        total = metrics['total_forms']
        unembedded_percentage = metrics['unembedded_percentage']
        thresholds = self.scoring_thresholds['forms']
        
        if (total >= thresholds['excellent']['total'][0] and
            unembedded_percentage <= thresholds['excellent']['unembedded_percentage'][1]):
            return 5.0
        elif (thresholds['good']['total'][0] <= total <= thresholds['good']['total'][1] and
              unembedded_percentage <= thresholds['good']['unembedded_percentage'][1]):
            return 3.5
        else:
            return 2.0
    
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
        if metrics['unused_percentage'] > 25:
            recommendations.append("Clean up unused custom properties to improve data quality")
        if metrics['total_custom_properties'] > 100:
            recommendations.append("Consider consolidating similar properties")
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
        """Get recommendations for forms category"""
        recommendations = []
        if metrics['total_forms'] < 3:
            recommendations.append("Create more forms to capture leads effectively")
        if metrics['unembedded_percentage'] > 40:
            recommendations.append("Embed or publish more forms to maximize lead capture")
        return recommendations
    
    def _get_forms_critical_issues(self, metrics: Dict) -> List[str]:
        """Get critical issues for forms category"""
        issues = []
        if metrics['total_forms'] == 0:
            issues.append("No forms found - lead capture system missing")
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
    
    def _empty_category_result(self) -> Dict:
        """Return empty result structure for failed category audits"""
        return {
            'score': 0,
            'grade': 'F',
            'metrics': {},
            'recommendations': ['Unable to audit this category - please check API permissions'],
            'critical_issues': ['Audit failed - API access issue']
        }
