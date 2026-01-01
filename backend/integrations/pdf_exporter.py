"""
PDF Exporter using ReportLab

Generates detailed design reports for transformers.
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.units import inch

class PDFExporter:
    """PDF generation for transformer designs."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = self.styles['Heading1']
        self.heading_style = self.styles['Heading2']
        self.normal_style = self.styles['Normal']
        self.table_header_style = ParagraphStyle(
            'TableHeader',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            alignment=1  # Center
        )

    def create_pdf_report(self, design_result: dict, requirements: dict) -> bytes:
        """
        Create a PDF report in memory.

        Args:
            design_result: Complete design output
            requirements: Design requirements

        Returns:
            PDF bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        story = []

        # 1. Title Page / Header
        app_type = design_result.get('application', 'Power Transformer').replace('_', ' ').title()
        core_part = design_result.get('core', {}).get('part_number', 'Unknown Core')

        story.append(Paragraph(f"{app_type} Design Report", self.title_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Design Ref: {core_part}", self.normal_style))
        story.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", self.normal_style))
        story.append(Spacer(1, 24))

        # 2. Specifications
        story.append(Paragraph("1. Design Requirements", self.heading_style))
        story.append(Spacer(1, 12))

        req_data = []
        # Flatten requirements for table
        for k, v in requirements.items():
            if isinstance(v, (str, int, float, bool)):
                req_data.append([str(k).replace('_', ' ').title(), str(v)])

        if req_data:
            t = Table(req_data, colWidths=[2.5*inch, 3.5*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(t)

        story.append(Spacer(1, 24))

        # 3. Core Selection
        story.append(Paragraph("2. Core Selection", self.heading_style))
        story.append(Spacer(1, 12))

        core = design_result.get('core', {})
        core_data = [
            ["Part Number", str(core.get('part_number', 'N/A'))],
            ["Manufacturer", str(core.get('manufacturer', 'N/A'))],
            ["Material", str(core.get('material', 'N/A'))],
            ["Geometry", str(core.get('geometry', 'N/A'))],
            ["Ae (Effective Area)", f"{core.get('Ae_cm2', 0)} cm²"],
            ["Ap (Area Product)", f"{core.get('Ap_cm4', 0)} cm⁴"],
        ]

        t_core = Table(core_data, colWidths=[2.5*inch, 3.5*inch])
        t_core.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ]))
        story.append(t_core)
        story.append(Spacer(1, 24))

        # 4. Winding Details
        story.append(Paragraph("3. Winding Details", self.heading_style))
        story.append(Spacer(1, 12))

        winding_header = ["Parameter", "Primary", "Secondary"]
        primary = design_result.get('primary', {})
        secondary = design_result.get('secondary', {})

        winding_data = [
            winding_header,
            ["Turns", str(primary.get('turns', 0)), str(secondary.get('turns', 0))],
            ["Wire Type", str(primary.get('wire_type', '-')), str(secondary.get('wire_type', '-'))],
            ["Wire Size", str(primary.get('wire_awg', primary.get('wire_width_mm', '-'))),
                          str(secondary.get('wire_awg', secondary.get('wire_width_mm', '-')))],
            ["Layers", str(primary.get('layers', 0)), str(secondary.get('layers', 0))],
            ["DC Resistance", f"{primary.get('Rdc_mOhm', 0)} mΩ", f"{secondary.get('Rdc_mOhm', 0)} mΩ"],
            ["Inductance", f"{primary.get('inductance_uH', 0)} µH", f"{secondary.get('inductance_uH', 0)} µH"],
        ]

        t_wind = Table(winding_data, colWidths=[2*inch, 2*inch, 2*inch])
        t_wind.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ]))
        story.append(t_wind)
        story.append(Spacer(1, 24))

        # 5. Performance / Losses
        story.append(Paragraph("4. Performance Analysis", self.heading_style))
        story.append(Spacer(1, 12))

        loss_data = [
            ["Core Loss", f"{design_result.get('core_loss_mW', design_result.get('core_loss_W', 0) * 1000):.1f} mW"],
            ["Copper Loss", f"{design_result.get('copper_loss_mW', design_result.get('copper_loss_W', 0) * 1000):.1f} mW"],
            ["Total Loss", f"{design_result.get('total_loss_mW', design_result.get('total_loss_W', 0) * 1000):.1f} mW"],
            ["Efficiency", f"{design_result.get('efficiency_percent', 0):.2f} %"],
            ["Temp Rise", f"{design_result.get('temperature_rise_C', design_result.get('temp_rise_C', 0)):.1f} °C"],
        ]

        t_loss = Table(loss_data, colWidths=[2.5*inch, 3.5*inch])
        t_loss.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.whitesmoke),
        ]))
        story.append(t_loss)
        story.append(Spacer(1, 24))

        # 6. Pulse Specifics (if available)
        pulse_resp = design_result.get('pulse_response')
        if pulse_resp:
            story.append(Paragraph("5. Pulse Response", self.heading_style))
            story.append(Spacer(1, 12))

            pulse_data = [
                ["Rise Time", f"{pulse_resp.get('rise_time_ns', 0)} ns"],
                ["Fall Time", f"{pulse_resp.get('fall_time_ns', 0)} ns"],
                ["Droop", f"{pulse_resp.get('droop_percent', 0)} %"],
                ["Backswing", f"{pulse_resp.get('backswing_percent', 0)} %"],
                ["Overshoot", f"{pulse_resp.get('overshoot_percent', 0)} %"],
            ]
            t_pulse = Table(pulse_data, colWidths=[2.5*inch, 3.5*inch])
            t_pulse.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(t_pulse)
            story.append(Spacer(1, 24))

        # 7. Verification
        verification = design_result.get('verification')
        if verification:
            story.append(Paragraph("6. Verification", self.heading_style))
            story.append(Spacer(1, 12))

            meets = verification.get('meets_specifications', False)
            status_color = colors.green if meets else colors.red
            status_text = "PASS" if meets else "FAIL"

            story.append(Paragraph(f"Design Status: <font color={status_color}>{status_text}</font>", self.heading_style))

            warnings = verification.get('warnings', [])
            if warnings:
                story.append(Spacer(1, 12))
                story.append(Paragraph("Warnings:", self.table_header_style))
                for w in warnings:
                    story.append(Paragraph(f"• {w}", self.normal_style))

        # Build PDF
        doc.build(story)

        buffer.seek(0)
        return buffer.getvalue()
