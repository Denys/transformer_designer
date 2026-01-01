"""
SVG Exporter

Generates cross-sectional visualizations of transformer windings.
"""

import math

class SVGExporter:
    """Generates SVG visualizations for transformer designs."""

    def __init__(self):
        pass

    def generate_winding_cross_section(self, design_result: dict, requirements: dict) -> str:
        """
        Generate an SVG string representing the winding cross-section.

        Args:
            design_result: Design result dictionary
            requirements: Design requirements dictionary

        Returns:
            SVG string
        """
        core = design_result.get('core', {})
        # We need window dimensions. These are usually in 'core' or inferred from Ap/Wa
        # Mocking window dimensions if not present, based on Wa
        Wa_cm2 = core.get('Wa_cm2', 1.0)
        # Assume E core aspect ratio 3:1 for window height:width approx?
        # Wa = h * w. h = 3w -> 3w^2 = Wa -> w = sqrt(Wa/3).
        # Let's use generic dimensions if specific ones aren't available
        window_width_mm = core.get('window_width_mm', math.sqrt(Wa_cm2 * 100 / 3) * 10)
        window_height_mm = core.get('window_height_mm', window_width_mm * 3)

        # Scaling
        scale = 10 # pixels per mm
        width_px = window_width_mm * scale
        height_px = window_height_mm * scale

        # Margins for SVG canvas
        svg_width = width_px + 100
        svg_height = height_px + 100

        svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width}" height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}">']
        svg.append(f'<rect width="100%" height="100%" fill="white"/>')

        # Draw Core Window (Bobbin area)
        start_x = 50
        start_y = 50
        svg.append(f'<rect x="{start_x}" y="{start_y}" width="{width_px}" height="{height_px}" fill="#f0f0f0" stroke="black" stroke-width="2"/>')

        # Draw Bobbin (Plastic)
        bobbin_thickness = 1.0 * scale
        svg.append(f'<rect x="{start_x + bobbin_thickness}" y="{start_y + bobbin_thickness}" width="{width_px - 2*bobbin_thickness}" height="{height_px - 2*bobbin_thickness}" fill="none" stroke="blue" stroke-width="1"/>')

        # Draw Primary Winding
        primary = design_result.get('primary', {})
        pri_turns = primary.get('turns', 10)
        pri_layers = primary.get('layers', 1)
        # Assume primary is inner

        # Height of primary block
        # We don't have exact build dimensions in the simple result dict usually, but let's estimate
        # Fill factor assumption
        fill_y = (height_px - 2*bobbin_thickness) * 0.9 # 90% usable height

        # Calculate radial build (width in x direction)
        # Simple estimation based on layers and wire size
        # Or just visual representation proportional to turns ratio/power?
        # Better: use wire_diameter if available
        pri_wire_dia = primary.get('wire_diameter_mm', 0.5) * scale
        pri_build = pri_layers * pri_wire_dia

        pri_x = start_x + bobbin_thickness
        pri_y = start_y + bobbin_thickness + (height_px - 2*bobbin_thickness - fill_y)/2 # Centered vertically

        svg.append(f'<rect x="{pri_x}" y="{pri_y}" width="{pri_build}" height="{fill_y}" fill="#b87333" stroke="none" opacity="0.8"/>')
        svg.append(f'<text x="{pri_x + pri_build/2}" y="{pri_y + fill_y/2}" font-family="Arial" font-size="12" fill="white" text-anchor="middle">Primary</text>')

        # Insulation
        ins_thickness = 0.5 * scale # 0.5mm
        ins_x = pri_x + pri_build
        svg.append(f'<rect x="{ins_x}" y="{pri_y}" width="{ins_thickness}" height="{fill_y}" fill="yellow" stroke="none"/>')

        # Secondary Winding
        sec = design_result.get('secondary', {})
        sec_layers = sec.get('layers', 1)
        sec_wire_dia = sec.get('wire_diameter_mm', 0.5) * scale
        sec_build = sec_layers * sec_wire_dia

        sec_x = ins_x + ins_thickness
        svg.append(f'<rect x="{sec_x}" y="{pri_y}" width="{sec_build}" height="{fill_y}" fill="#b87333" stroke="none" opacity="0.6"/>')
        svg.append(f'<text x="{sec_x + sec_build/2}" y="{pri_y + fill_y/2}" font-family="Arial" font-size="12" fill="white" text-anchor="middle">Secondary</text>')

        # Labels
        svg.append(f'<text x="{start_x + width_px/2}" y="{start_y - 10}" font-family="Arial" font-size="14" text-anchor="middle">Winding Cross-Section (Window View)</text>')

        svg.append('</svg>')
        return "\n".join(svg)
