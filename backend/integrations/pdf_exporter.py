"""
PDF Exporter

Exports transformer design reports to PDF using ReportLab.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from io import BytesIO
from typing import Dict, Any, List
from datetime import datetime

class PDFExporter:
    """
    Exports transformer designs to PDF format.
    """

    def __init__(self):
        pass

    def export_pdf(
        self,
        design_result: Dict[str, Any],
        requirements: Dict[str, Any],
    ) -> bytes:
        """
        Generate PDF report for the transformer design.

        Args:
            design_result: Complete transformer design
            requirements: Design requirements

        Returns:
            PDF file content as bytes
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Styles
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        heading1_style = styles['Heading1']
        heading2_style = styles['Heading2']
        normal_style = styles['Normal']

        # Custom styles
        value_style = ParagraphStyle(
            'Value',
            parent=normal_style,
            fontName='Helvetica-Bold',
        )

        elements = []

        # Title
        elements.append(Paragraph("Transformer Design Report", title_style))
        elements.append(Spacer(1, 0.25 * inch))

        # Header Info
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elements.append(Paragraph(f"Generated on: {date_str}", normal_style))
        elements.append(Spacer(1, 0.25 * inch))

        # 1. Design Requirements
        elements.append(Paragraph("1. Design Requirements", heading1_style))

        req_data = [
            ["Parameter", "Value", "Unit"],
            ["Output Power", f"{requirements.get('output_power_W', 0)}", "W"],
            ["Primary Voltage", f"{requirements.get('primary_voltage_V', 0)}", "V"],
            ["Secondary Voltage", f"{requirements.get('secondary_voltage_V', 0)}", "V"],
            ["Frequency", f"{requirements.get('frequency_Hz', 0)}", "Hz"],
            ["Efficiency Target", f"{requirements.get('efficiency_percent', 0)}", "%"],
            ["Topology", f"{requirements.get('transformer_type', 'N/A')}", ""],
            ["Waveform", f"{requirements.get('waveform', 'sinusoidal')}", ""],
            ["Design Method", f"{requirements.get('design_method', 'N/A')}", ""],
        ]

        elements.append(self._create_table(req_data))
        elements.append(Spacer(1, 0.2 * inch))

        # 2. Core Selection
        elements.append(Paragraph("2. Core Selection", heading1_style))

        core = design_result.get('core', {})
        core_data = [
            ["Parameter", "Value", "Unit"],
            ["Manufacturer", f"{core.get('manufacturer', 'N/A')}", ""],
            ["Part Number", f"{core.get('part_number', 'N/A')}", ""],
            ["Material", f"{core.get('material', 'N/A')}", ""],
            ["Geometry", f"{core.get('geometry', 'N/A')}", ""],
            ["Ae (Effective Area)", f"{core.get('Ae_cm2', 0):.4f}", "cm²"],
            ["Wa (Window Area)", f"{core.get('Wa_cm2', 0):.4f}", "cm²"],
            ["Ap (Area Product)", f"{core.get('Ap_cm4', 0):.4f}", "cm⁴"],
            ["Ve (Volume)", f"{core.get('Ve_cm3', 0):.4f}", "cm³"],
        ]

        elements.append(self._create_table(core_data))
        elements.append(Spacer(1, 0.2 * inch))

        # 3. Winding Design
        elements.append(Paragraph("3. Winding Design", heading1_style))

        winding = design_result.get('winding', {})

        # Primary
        elements.append(Paragraph("Primary Winding", heading2_style))
        pri_data = [
            ["Parameter", "Value"],
            ["Turns", f"{winding.get('primary_turns', 0)}"],
            ["Wire Type", f"{winding.get('primary_wire_type', 'solid')}"],
            ["Wire Size", f"{winding.get('primary_wire_awg', 0)} AWG"],
            ["Strands", f"{winding.get('primary_strands', 1)}"],
            ["Layers", f"{winding.get('primary_layers', 1)}"],
            ["DC Resistance", f"{winding.get('primary_Rdc_mOhm', 0):.2f} mΩ"],
        ]
        elements.append(self._create_table(pri_data, col_widths=[2.5*inch, 2.5*inch]))
        elements.append(Spacer(1, 0.1 * inch))

        # Secondary
        elements.append(Paragraph("Secondary Winding", heading2_style))
        sec_data = [
            ["Parameter", "Value"],
            ["Turns", f"{winding.get('secondary_turns', 0)}"],
            ["Wire Type", f"{winding.get('secondary_wire_type', 'solid')}"],
            ["Wire Size", f"{winding.get('secondary_wire_awg', 0)} AWG"],
            ["Strands", f"{winding.get('secondary_strands', 1)}"],
            ["Layers", f"{winding.get('secondary_layers', 1)}"],
            ["DC Resistance", f"{winding.get('secondary_Rdc_mOhm', 0):.2f} mΩ"],
        ]
        elements.append(self._create_table(sec_data, col_widths=[2.5*inch, 2.5*inch]))
        elements.append(Spacer(1, 0.1 * inch))

        # 4. Performance Analysis
        elements.append(Paragraph("4. Performance Analysis", heading1_style))

        losses = design_result.get('losses', {})
        thermal = design_result.get('thermal', {})

        perf_data = [
            ["Parameter", "Value", "Unit"],
            ["Total Loss", f"{losses.get('total_loss_W', 0):.2f}", "W"],
            ["Efficiency", f"{losses.get('efficiency_percent', 0):.2f}", "%"],
            ["Core Loss", f"{losses.get('core_loss_W', 0):.2f}", "W"],
            ["Copper Loss", f"{losses.get('total_copper_loss_W', 0):.2f}", "W"],
            ["Temp Rise", f"{thermal.get('temperature_rise_C', 0):.1f}", "°C"],
            ["Hotspot Temp", f"{thermal.get('hotspot_temp_C', 0):.1f}", "°C"],
        ]

        elements.append(self._create_table(perf_data))
        elements.append(Spacer(1, 0.2 * inch))

        # 5. Electrical Parameters
        elements.append(Paragraph("5. Electrical Parameters", heading1_style))

        elec_data = [
            ["Parameter", "Value", "Unit"],
            ["Magnetizing Inductance", f"{design_result.get('magnetizing_inductance_uH', 0):.2f}", "µH"],
            ["Leakage Inductance", f"{design_result.get('leakage_inductance_uH', 0):.2f}", "µH"],
            ["Turns Ratio", f"{design_result.get('turns_ratio', 0):.3f}", ""],
        ]

        elements.append(self._create_table(elec_data))

        # Build PDF
        doc.build(elements)

        pdf_content = buffer.getvalue()
        buffer.close()
        return pdf_content

    def _create_table(self, data: List[List[str]], col_widths=None):
        """Helper to create styled tables."""
        t = Table(data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ]))
        return t
