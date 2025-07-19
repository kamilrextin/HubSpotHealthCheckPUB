import io
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import Color, blue, red, green, orange
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

class PDFGenerator:
    """Generate PDF reports for HubSpot audit results"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Create custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=blue
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=blue
        ))
        
        self.styles.add(ParagraphStyle(
            name='ScoreText',
            parent=self.styles['Normal'],
            fontSize=14,
            spaceAfter=6
        ))
    
    def generate_report(self, audit_results: dict) -> io.BytesIO:
        """Generate complete PDF audit report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # Build the story (content)
        story = []
        
        # Title
        story.append(Paragraph("HubSpot Marketing Operations Audit Report", self.styles['CustomTitle']))
        story.append(Spacer(1, 20))
        
        # Report metadata
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y')}", self.styles['Normal']))
        story.append(Spacer(1, 10))
        
        # Overall score section
        overall_score = audit_results.get('overall_score', 0)
        overall_grade = audit_results.get('overall_grade', 'F')
        
        story.append(Paragraph("Overall Assessment", self.styles['SectionHeader']))
        story.append(Paragraph(f"Overall Score: {overall_score}/5.0 (Grade: {overall_grade})", self.styles['ScoreText']))
        story.append(Spacer(1, 20))
        
        # Summary table
        summary_data = [['Category', 'Score', 'Grade', 'Status']]
        categories = ['admin', 'properties', 'workflows', 'forms', 'reporting', 'sales']
        category_names = {
            'admin': 'Admin & Setup',
            'properties': 'Properties',
            'workflows': 'Workflows',
            'forms': 'Forms',
            'reporting': 'Reporting',
            'sales': 'Sales'
        }
        
        for category in categories:
            if category in audit_results and isinstance(audit_results[category], dict):
                cat_data = audit_results[category]
                score = cat_data.get('score', 0)
                grade = cat_data.get('grade', 'F')
                status = self._get_status_from_grade(grade)
                summary_data.append([category_names[category], f"{score}/5.0", grade, status])
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), Color(1, 1, 1)),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), Color(0.95, 0.95, 0.95)),
            ('GRID', (0, 0), (-1, -1), 1, Color(0, 0, 0))
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 30))
        
        # Detailed category breakdowns
        for category in categories:
            if category in audit_results and isinstance(audit_results[category], dict):
                story.extend(self._generate_category_section(category_names[category], audit_results[category]))
        
        # Recommendations summary
        story.append(Paragraph("Key Recommendations", self.styles['SectionHeader']))
        all_recommendations = []
        for category in categories:
            if category in audit_results and isinstance(audit_results[category], dict):
                recommendations = audit_results[category].get('recommendations', [])
                all_recommendations.extend(recommendations)
        
        for i, recommendation in enumerate(all_recommendations[:10], 1):  # Top 10 recommendations
            story.append(Paragraph(f"{i}. {recommendation}", self.styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        # Footer
        story.append(Paragraph("For questions about this audit or to schedule a strategy consultation, please contact our team.", self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def _generate_category_section(self, category_name: str, category_data: dict):
        """Generate content for a single category section"""
        content = []
        
        content.append(Paragraph(category_name, self.styles['SectionHeader']))
        
        # Score and grade
        score = category_data.get('score', 0)
        grade = category_data.get('grade', 'F')
        content.append(Paragraph(f"Score: {score}/5.0 (Grade: {grade})", self.styles['ScoreText']))
        
        # Metrics
        metrics = category_data.get('metrics', {})
        if metrics:
            content.append(Paragraph("Key Metrics:", self.styles['Normal']))
            for key, value in metrics.items():
                formatted_key = key.replace('_', ' ').title()
                content.append(Paragraph(f"• {formatted_key}: {value}", self.styles['Normal']))
        
        # Critical issues
        critical_issues = category_data.get('critical_issues', [])
        if critical_issues:
            content.append(Paragraph("Critical Issues:", self.styles['Normal']))
            for issue in critical_issues:
                content.append(Paragraph(f"⚠ {issue}", self.styles['Normal']))
        
        # Recommendations
        recommendations = category_data.get('recommendations', [])
        if recommendations:
            content.append(Paragraph("Recommendations:", self.styles['Normal']))
            for rec in recommendations:
                content.append(Paragraph(f"• {rec}", self.styles['Normal']))
        
        content.append(Spacer(1, 20))
        return content
    
    def _get_status_from_grade(self, grade: str) -> str:
        """Convert grade to status description"""
        status_map = {
            'A': 'Excellent',
            'B': 'Good',
            'C': 'Fair',
            'D': 'Needs Improvement',
            'F': 'Critical'
        }
        return status_map.get(grade, 'Unknown')
