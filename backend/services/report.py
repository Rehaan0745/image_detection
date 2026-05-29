import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("report_generator")

def generate_pdf_report(
    output_path: str,
    medicine_name: str,
    view_name: str,
    authenticity_score: float,
    risk_level: str,
    explanations: list,
    timestamp: str,
    inspector_id: str = "INSPECT-AI-01"
):
    """
    Generates a structured PDF inspection report for the tablet carton.
    """
    try:
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=54
        )
        
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            textColor=colors.HexColor("#1A365D"),  # Surgical Navy
            alignment=0,  # Left-aligned
            spaceAfter=20
        )
        
        header_style = ParagraphStyle(
            name="SectionHeader",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#2B6CB0"),  # Tech Blue
            spaceBefore=15,
            spaceAfter=10
        )
        
        body_style = ParagraphStyle(
            name="ReportBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#2D3748")  # Charcoal
        )
        
        bold_body_style = ParagraphStyle(
            name="ReportBodyBold",
            parent=body_style,
            fontName="Helvetica-Bold"
        )
        
        story = []
        
        # 1. Title Block
        story.append(Paragraph("Tablet Carton Inspection Report", title_style))
        story.append(Spacer(1, 10))
        
        # 2. Risk Level Colored Panel
        risk_colors = {
            "low": ("#C6F6D5", "#22543D", "LOW RISK (Authentic)"),
            "medium": ("#FEEBC8", "#744210", "MEDIUM RISK (Suspicious)"),
            "high": ("#FED7D7", "#742A2A", "HIGH RISK (Potential Counterfeit)")
        }
        bg_color, text_color, label = risk_colors.get(risk_level.lower(), ("#EDF2F7", "#2D3748", "UNKNOWN"))
        
        risk_table_data = [
            [
                Paragraph(f"<b>Authenticity Score: {authenticity_score:.1f}%</b>", bold_body_style),
                Paragraph(f"<b>Security Level: <font color='{text_color}'>{label}</font></b>", bold_body_style)
            ]
        ]
        
        risk_table = Table(risk_table_data, colWidths=[250, 250])
        risk_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(bg_color)),
            ('PADDING', (0,0), (-1,-1), 12),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 12),
            ('TOPPADDING', (0,0), (-1,-1), 12),
            ('INNERGRID', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E0")),
            ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor(text_color))
        ]))
        story.append(risk_table)
        story.append(Spacer(1, 20))
        
        # 3. Product and Metadata Block
        story.append(Paragraph("Inspection Details", header_style))
        metadata_data = [
            [Paragraph("<b>Medicine Name:</b>", body_style), Paragraph(medicine_name, body_style),
             Paragraph("<b>Packaging View:</b>", body_style), Paragraph(view_name.capitalize(), body_style)],
            [Paragraph("<b>Timestamp:</b>", body_style), Paragraph(timestamp, body_style),
             Paragraph("<b>Inspector ID:</b>", body_style), Paragraph(inspector_id, body_style)],
        ]
        metadata_table = Table(metadata_data, colWidths=[100, 150, 100, 150])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")),
            ('PADDING', (0,0), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ]))
        story.append(metadata_table)
        story.append(Spacer(1, 20))
        
        # 4. Anomaly Log Table
        story.append(Paragraph("Detected Anomalies and Visual Differences", header_style))
        
        if not explanations:
            story.append(Paragraph("No anomalies detected. The query packaging matches the authentic reference image specifications.", body_style))
        else:
            table_header_style = ParagraphStyle(
                name="TableHeader",
                parent=body_style,
                fontName="Helvetica-Bold",
                textColor=colors.white
            )
            
            # Anomaly details
            anomaly_data = [[
                Paragraph("No.", table_header_style),
                Paragraph("Category", table_header_style),
                Paragraph("Severity", table_header_style),
                Paragraph("Technical Explanation", table_header_style)
            ]]
            
            severity_colors = {
                "critical": "#E53E3E",   # Soft Red
                "suspicious": "#DD6B20", # Soft Orange
                "minor": "#D69E2E"       # Soft Yellow
            }
            
            for idx, item in enumerate(explanations):
                sev = item["severity"].lower()
                sev_color = severity_colors.get(sev, "#4A5568")
                
                anomaly_data.append([
                    Paragraph(str(idx + 1), body_style),
                    Paragraph(item["category"], body_style),
                    Paragraph(f"<b><font color='{sev_color}'>{sev.upper()}</font></b>", body_style),
                    Paragraph(item["text"], body_style)
                ])
                
            anomaly_table = Table(anomaly_data, colWidths=[30, 100, 80, 290])
            anomaly_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1A365D")),
                ('PADDING', (0,0), (-1,-1), 8),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F7FAFC")]),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
            ]))
            story.append(anomaly_table)
            
        story.append(Spacer(1, 30))
        
        # 5. Conclusion & Verification Signature
        story.append(Paragraph("Authorized Inspection Verification", header_style))
        story.append(Paragraph("This report was compiled offline using visual feature matching, optical character verification, and deep regional visual comparison algorithms. The output reflects structural and semantic packaging discrepancies and is intended for quality assurance verification.", body_style))
        
        story.append(Spacer(1, 30))
        sig_data = [
            [Paragraph("<b>Inspection Conducted By:</b>", body_style), Paragraph("<b>Signature:</b>", body_style)],
            [Paragraph(f"System Operator ID: {inspector_id}", body_style), Paragraph("___________________________", body_style)],
            [Paragraph(f"Verification Date: {timestamp[:10]}", body_style), Paragraph("QA Lead Inspector", body_style)]
        ]
        sig_table = Table(sig_data, colWidths=[250, 250])
        sig_table.setStyle(TableStyle([
            ('PADDING', (0,0), (-1,-1), 4),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(sig_table)
        
        # Build PDF
        doc.build(story)
        logger.info(f"PDF Inspection Report successfully saved to: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to generate PDF report: {e}")
        return False
