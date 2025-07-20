#!/usr/bin/env python3
"""AI-powered analysis and report generation for HubSpot audits"""

import os
import json
import logging
from typing import Dict, List
from openai import OpenAI

class AIAnalyzer:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
    def generate_comprehensive_report(self, audit_results: Dict) -> Dict:
        """Generate AI-enhanced comprehensive audit report"""
        try:
            # Extract key metrics for AI analysis
            summary_data = self._extract_summary_data(audit_results)
            
            # Generate AI summary
            ai_summary = self._generate_ai_summary(summary_data)
            
            # Generate strategic recommendations
            ai_recommendations = self._generate_strategic_recommendations(summary_data)
            
            # Generate action plan
            action_plan = self._generate_action_plan(summary_data)
            
            return {
                'ai_summary': ai_summary,
                'ai_recommendations': ai_recommendations,
                'action_plan': action_plan,
                'executive_summary': self._generate_executive_summary(summary_data),
                'risk_assessment': self._generate_risk_assessment(summary_data)
            }
            
        except Exception as e:
            logging.error(f"AI analysis error: {str(e)}")
            return {
                'ai_summary': "AI analysis temporarily unavailable",
                'ai_recommendations': ["Review audit results manually for immediate insights"],
                'action_plan': [],
                'executive_summary': "Standard audit completed successfully",
                'risk_assessment': "Manual review required"
            }
    
    def _extract_summary_data(self, audit_results: Dict) -> Dict:
        """Extract key data points for AI analysis"""
        summary = {
            'overall_score': audit_results.get('overall_score', 0),
            'overall_grade': audit_results.get('overall_grade', 'F'),
            'categories': {}
        }
        
        for category, data in audit_results.items():
            if isinstance(data, dict) and 'score' in data:
                summary['categories'][category] = {
                    'score': data.get('score', 0),
                    'grade': data.get('grade', 'F'),
                    'metrics': data.get('metrics', {}),
                    'critical_issues': data.get('critical_issues', []),
                    'recommendations': data.get('recommendations', [])
                }
        
        return summary
    
    def _generate_ai_summary(self, data: Dict) -> str:
        """Generate AI-powered executive summary"""
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        prompt = f"""
        Based on this HubSpot Marketing Operations audit data, write a comprehensive executive summary.
        
        Overall Score: {data['overall_score']}/5.0 (Grade: {data['overall_grade']})
        
        Category Breakdown:
        {json.dumps(data['categories'], indent=2)}
        
        Write a professional 3-4 paragraph executive summary that:
        1. Summarizes the current state of their HubSpot setup
        2. Highlights the most critical findings
        3. Identifies the biggest opportunities for improvement
        4. Provides strategic context for the recommendations
        
        Use a professional, consultative tone suitable for marketing executives.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"AI summary generation error: {str(e)}")
            return "AI-generated summary temporarily unavailable."
    
    def _generate_strategic_recommendations(self, data: Dict) -> List[str]:
        """Generate strategic AI recommendations"""
        prompt = f"""
        Based on this HubSpot audit data, provide 5-7 strategic recommendations prioritized by impact.
        
        Audit Data: {json.dumps(data, indent=2)}
        
        For each recommendation:
        1. Focus on high-impact improvements
        2. Consider the interconnections between different areas
        3. Prioritize based on the overall score and critical issues
        4. Make recommendations specific and actionable
        
        Format as a JSON array of strings, each recommendation being actionable and specific.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=600,
                temperature=0.6
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get('recommendations', [])
        except Exception as e:
            logging.error(f"AI recommendations error: {str(e)}")
            return ["Review audit findings and implement highest priority improvements"]
    
    def _generate_action_plan(self, data: Dict) -> List[Dict]:
        """Generate prioritized action plan with timelines"""
        prompt = f"""
        Create a prioritized action plan based on this HubSpot audit data.
        
        Data: {json.dumps(data, indent=2)}
        
        Generate 8-10 action items with:
        - priority (High/Medium/Low)
        - timeline (Immediate/Short-term/Long-term)
        - effort (Low/Medium/High)
        - impact (Low/Medium/High)
        - category (which audit area it addresses)
        
        Return as JSON array of objects with these fields.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=800,
                temperature=0.5
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get('action_plan', [])
        except Exception as e:
            logging.error(f"AI action plan error: {str(e)}")
            return []
    
    def _generate_executive_summary(self, data: Dict) -> str:
        """Generate brief executive summary for dashboard"""
        overall_score = data.get('overall_score', 0)
        grade = data.get('overall_grade', 'F')
        
        if overall_score >= 4.0:
            return f"Excellent HubSpot setup (Grade {grade}). Your marketing operations are well-optimized with minimal areas for improvement."
        elif overall_score >= 3.0:
            return f"Good HubSpot foundation (Grade {grade}) with several optimization opportunities to maximize your marketing effectiveness."
        elif overall_score >= 2.0:
            return f"Developing HubSpot setup (Grade {grade}) with significant opportunities to improve lead generation and automation efficiency."
        else:
            return f"HubSpot setup needs attention (Grade {grade}). Critical gaps in your marketing operations require immediate focus."
    
    def _generate_risk_assessment(self, data: Dict) -> str:
        """Generate risk assessment based on audit findings"""
        critical_issues_count = sum(
            len(cat_data.get('critical_issues', [])) 
            for cat_data in data.get('categories', {}).values()
        )
        
        if critical_issues_count == 0:
            return "Low Risk: No critical issues identified in your HubSpot setup."
        elif critical_issues_count <= 3:
            return f"Medium Risk: {critical_issues_count} critical issues require attention to prevent lead generation gaps."
        else:
            return f"High Risk: {critical_issues_count} critical issues could significantly impact your marketing performance."