"""Canonical Fastener Label Specification and Vector SVG Renderer.

Provides a unified, high-contrast label layout with color-coded taxonomy accent bar,
part title, thread/pitch subtext, drive/head silhouette icons, and scannable QR code matrix.
"""

from __future__ import annotations

import re
import xml.sax.saxutils as sax
from dataclasses import dataclass
from typing import Any, Optional
import qrcode
from qrcode.main import QRCode

from hardware.labels.vector_icons import get_component_icon_svg, get_drive_icon_svg, get_head_icon_svg

# Default Finished Cut Label Geometry (mm)
STRIP_W = 34.00
STRIP_H = 10.00
STRIP_R = 1.00

# Bleed Geometry (+1.0 mm all sides)
BLEED = 1.00
BLEED_W = STRIP_W + 2 * BLEED  # 36.00 mm
BLEED_H = STRIP_H + 2 * BLEED  # 12.00 mm
BLEED_R = STRIP_R + BLEED      # 2.00 mm


def clean_id(prefix: str, *parts: Any) -> str:
    """Generate a valid XML ID slug without spaces, quotes, or special characters."""
    raw = "_".join(str(p) for p in parts if p)
    slug = re.sub(r"[^a-zA-Z0-9_-]", "_", f"{prefix}_{raw}")
    return re.sub(r"_+", "_", slug).strip("_")


def escape_xml(s: Any) -> str:
    """Escape XML special characters in text nodes (&, <, >, quotes)."""
    return sax.escape(str(s) if s is not None else "", {'"': "&quot;", "'": "&apos;"})


@dataclass
class LabelData:
    """Canonical specification for a fastener / component storage bin label."""
    part_id: str
    name: str = ""
    size: str = ""
    length: str = ""
    head: str = "shcs"
    drive: str = "hex"
    comp_type: str = "bolt"
    pitch: str = ""
    tap_drill: str = ""
    clearance_drill: str = ""
    tool_key: str = ""
    material: str = ""
    accent_color: str = "#0077CC"
    bg_color: str = "#FFFFFF"
    extra_note: str = ""
    bin_id: str = ""
    qr_payload: str = ""

    def __post_init__(self):
        if not self.qr_payload and self.part_id:
            self.qr_payload = f"http://tasker-pi.local:8090/p/{self.part_id}"


def generate_qr_svg_path(payload: str, size: float = 7.5, x: float = 0.0, y: float = 0.0, color: str = "#111111") -> str:
    """
    Generate a pure vector SVG path representation of a QR code.
    Encodes standard actionable URLs with a 1-module quiet zone border for instant phone camera scanning.
    """
    if not payload:
        return ""

    qr = QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=1,
        border=1,  # Standard 1-module quiet zone for phone camera optical detection
    )
    qr.add_data(payload)
    qr.make(fit=True)
    matrix = qr.get_matrix()

    module_count = len(matrix)
    if module_count == 0:
        return ""

    cell_size = size / float(module_count)
    path_segments = []

    for r_idx, row in enumerate(matrix):
        for c_idx, cell in enumerate(row):
            if cell:
                cx = x + c_idx * cell_size
                cy = y + r_idx * cell_size
                path_segments.append(
                    f"M {cx:.3f},{cy:.3f} h {cell_size:.3f} v {cell_size:.3f} h -{cell_size:.3f} Z"
                )

    path_data = " ".join(path_segments)
    return f'<g class="qr-code"><rect x="{x:.3f}" y="{y:.3f}" width="{size:.3f}" height="{size:.3f}" fill="#FFFFFF"/><path d="{path_data}" fill="{color}"/></g>'


def render_keepout_text(
    text: str,
    x: float,
    y: float,
    base_font_size: float,
    max_width: float,
    font_weight: str = "normal",
    fill: str = "#111111",
) -> str:
    """
    Render SVG text with strict keepout enforcement.
    Dynamically scales font size and applies SVG textLength glyph compression
    so text never crosses into icon, QR code, or margin keepout zones.
    """
    if not text:
        return ""

    escaped = escape_xml(text)
    char_factor = 0.58 if font_weight == "bold" else 0.50
    est_width = len(text) * base_font_size * char_factor

    font_size = base_font_size
    text_length_attr = ""

    if est_width > max_width and max_width > 0:
        # Dynamically scale font down proportionally
        scale = max_width / est_width
        font_size = max(base_font_size * scale, base_font_size * 0.70)

        # Apply SVG textLength compression if still near or exceeding limit
        new_est = len(text) * font_size * char_factor
        if new_est > max_width * 0.90:
            text_length_attr = f' textLength="{max_width:.2f}" lengthAdjust="spacingAndGlyphs"'

    return (
        f'<text x="{x:.2f}" y="{y:.2f}" font-family="Arial, Helvetica, sans-serif" '
        f'font-weight="{font_weight}" font-size="{font_size:.2f}" fill="{fill}"{text_length_attr}>{escaped}</text>'
    )


def format_label_strings(spec: LabelData) -> tuple[str, str, str]:
    """Format label text strings cleanly with standard concise nomenclature."""
    if spec.comp_type in ("nut", "nyloc"):
        suffix = spec.length.replace(" Nut", "").strip() if spec.length else "Nut"
        title = f"{spec.size} {suffix}".strip()
        sub1 = spec.pitch if spec.pitch else ""
        sub2 = f"Key {spec.tool_key}" if spec.tool_key else spec.material
    elif spec.comp_type in ("washer", "split"):
        suffix = spec.length.replace(" Washer", "").strip() if spec.length else "Washer"
        title = f"{spec.size} {suffix}".strip()
        sub1 = spec.extra_note or ""
        sub2 = spec.material or ""
    elif spec.comp_type == "insert":
        len_str = spec.length.replace("L: ", "").strip()
        title = f"{spec.size} × {len_str}".strip() if len_str else spec.size
        sub1 = spec.extra_note.replace("Hole: ", "").strip() if spec.extra_note else ""
        sub2 = "Brass Insert"
    elif spec.comp_type == "pin":
        title = f"{spec.size} × {spec.length}".strip() if spec.length else spec.size
        sub1 = spec.extra_note or "Dowel Pin"
        sub2 = spec.material or "Hardened Steel"
    elif spec.comp_type == "standoff":
        title = f"{spec.size} × {spec.length}".strip() if spec.length else spec.size
        sub1 = spec.extra_note or "Hex Standoff"
        sub2 = f"Key {spec.tool_key}" if spec.tool_key else spec.material
    else:
        title = f"{spec.size} × {spec.length}".strip() if spec.length else spec.size
        p_str = spec.pitch if spec.pitch else ""
        tap_str = spec.tap_drill.split()[0] if (spec.tap_drill and spec.tap_drill.split()) else ""
        sub1 = f"{p_str} | Tap {tap_str}" if (p_str and tap_str) else (spec.extra_note or p_str or tap_str)
        sub2 = f"Key {spec.tool_key}" if spec.tool_key else spec.material

    return title, sub1, sub2


def render_canonical_label_svg(
    spec: LabelData,
    x: float = 0.0,
    y: float = 0.0,
    width: float = STRIP_W,
    height: float = STRIP_H,
    corner_radius: float = STRIP_R,
    include_bleed: bool = False,
    include_qr: bool = True,
    qr_size: float = 7.0,
) -> str:
    """
    Render a canonical vector SVG label for a single fastener/part.
    Guarantees strict keepout areas between text, silhouette icons, and QR code matrix.
    """
    color = spec.accent_color or "#0077CC"
    bg = spec.bg_color or "#FFFFFF"
    main_title, sub1, sub2 = format_label_strings(spec)
    node_id = clean_id("lbl", spec.part_id or spec.size, int(x), int(y))
    clip_id = clean_id("clip", spec.part_id or spec.size, int(x), int(y))

    svg_parts = [
        f'<g id="{node_id}" transform="translate({x:.2f},{y:.2f})">'
    ]

    text_x = 4.20
    accent_w = 2.60

    if include_bleed:
        b_x = -BLEED
        b_y = -BLEED
        b_w = width + 2 * BLEED
        b_h = height + 2 * BLEED
        b_r = corner_radius + BLEED

        # Bleed background
        svg_parts.append(
            f'<rect x="{b_x:.2f}" y="{b_y:.2f}" width="{b_w:.2f}" height="{b_h:.2f}" rx="{b_r:.2f}" fill="{bg}" stroke="none"/>'
        )
        # Bleed accent bar on left
        svg_parts.append(
            f'<path d="M {b_x:.2f},{b_r + b_y:.2f} A {b_r:.2f},{b_r:.2f} 0 0,1 {b_r + b_x:.2f},{b_y:.2f} L {accent_w + BLEED:.2f},{b_y:.2f} L {accent_w + BLEED:.2f},{height + BLEED:.2f} L {b_r + b_x:.2f},{height + BLEED:.2f} A {b_r:.2f},{b_r:.2f} 0 0,1 {b_x:.2f},{height + BLEED - b_r:.2f} Z" fill="{color}"/>'
        )
    else:
        # Standard cut boundary
        svg_parts.append(
            f'<rect x="0" y="0" width="{width:.2f}" height="{height:.2f}" rx="{corner_radius:.2f}" fill="{bg}" stroke="#CCCCCC" stroke-width="0.2"/>'
        )
        # Standard left accent bar
        svg_parts.append(
            f'<path d="M 0,{corner_radius:.2f} A {corner_radius:.2f},{corner_radius:.2f} 0 0,1 {corner_radius:.2f},0 L {accent_w:.2f},0 L {accent_w:.2f},{height:.2f} L {corner_radius:.2f},{height:.2f} A {corner_radius:.2f},{corner_radius:.2f} 0 0,1 0,{height - corner_radius:.2f} Z" fill="{color}"/>'
        )

    # --------------------------------------------------------------------------
    # Layout Keepout & Geometry Calculations
    # --------------------------------------------------------------------------
    has_qr = include_qr and bool(spec.qr_payload)
    is_compact = width <= 40.0

    if is_compact:
        # Standard 34x10 mm strip label - optimized for print legibility
        if has_qr:
            effective_qr_sz = min(qr_size, height - 3.4)  # ~6.6 mm
            qr_x = width - effective_qr_sz - 1.0
            qr_y = (height - effective_qr_sz) / 2.0
            svg_parts.append(generate_qr_svg_path(spec.qr_payload, size=effective_qr_sz, x=qr_x, y=qr_y))

            icon_w = 5.6
            icon_h = 8.2
            icon_x = qr_x - icon_w - 1.0
            text_max_right = icon_x - 0.8
        else:
            icon_w = 7.2
            icon_h = 8.4
            icon_x = width - icon_w - 1.5
            text_max_right = icon_x - 1.0

        # Render Silhouette Icons (Bold & crisp for printing)
        if spec.comp_type in ("nut", "nyloc", "insert", "washer", "split"):
            comp_h = min(icon_h, 7.2)
            svg_parts.append(get_component_icon_svg(spec.comp_type, icon_x, (height - comp_h) / 2.0, icon_w, comp_h, color="#222222"))
        else:
            head_h = 4.4 if has_qr else 4.8
            drive_sz = 3.6 if has_qr else 4.0
            head_y = 0.8 if has_qr else 0.6
            drive_y = 5.4 if has_qr else 5.5
            drive_x = icon_x + (icon_w - drive_sz) / 2.0

            if spec.head and spec.head != "none":
                svg_parts.append(get_head_icon_svg(spec.head, icon_x, head_y, icon_w, head_h, color="#222222"))
            if spec.drive and spec.drive != "none":
                svg_parts.append(get_drive_icon_svg(spec.drive, drive_x, drive_y, drive_sz, color=color))

        title_y = 3.60
        sub1_y = 6.10
        sub2_y = 8.40
        base_title_sz = 2.7
        base_sub_sz = 1.55
    else:
        # Expanded Avery 5160 / Large Sheet Layout
        if has_qr:
            effective_qr_sz = min(qr_size, height - 6.0)
            qr_x = width - effective_qr_sz - 2.5
            qr_y = (height - effective_qr_sz) / 2.0
            svg_parts.append(generate_qr_svg_path(spec.qr_payload, size=effective_qr_sz, x=qr_x, y=qr_y))

            icon_w = 12.0
            icon_h = 18.0
            icon_x = qr_x - icon_w - 2.0
            text_max_right = icon_x - 1.5
        else:
            icon_w = 15.0
            icon_h = 18.0
            icon_x = width - icon_w - 3.0
            text_max_right = icon_x - 2.0

        # Render Silhouette Icons
        if spec.comp_type in ("nut", "nyloc", "insert", "washer", "split"):
            comp_h = min(icon_h, 16.0)
            svg_parts.append(get_component_icon_svg(spec.comp_type, icon_x, (height - comp_h) / 2.0, icon_w, comp_h, color="#222222"))
        else:
            head_h = 9.5
            drive_sz = 8.0
            head_y = 1.8
            drive_y = 11.8
            drive_x = icon_x + (icon_w - drive_sz) / 2.0

            if spec.head and spec.head != "none":
                svg_parts.append(get_head_icon_svg(spec.head, icon_x, head_y, icon_w, head_h, color="#222222"))
            if spec.drive and spec.drive != "none":
                svg_parts.append(get_drive_icon_svg(spec.drive, drive_x, drive_y, drive_sz, color=color))

        title_y = height * 0.35
        sub1_y = height * 0.60
        sub2_y = height * 0.84
        base_title_sz = height * 0.22
        base_sub_sz = height * 0.14

    max_text_w = max(5.0, text_max_right - text_x)

    # --------------------------------------------------------------------------
    # Text Zone with Clip-Path & Font Scaling Keepout Protection
    # --------------------------------------------------------------------------
    svg_parts.append(f'<defs><clipPath id="{clip_id}"><rect x="{text_x - 0.2:.2f}" y="0" width="{max_text_w + 0.4:.2f}" height="{height:.2f}"/></clipPath></defs>')
    svg_parts.append(f'<g clip-path="url(#{clip_id})">')

    # Main Title
    svg_parts.append(
        render_keepout_text(main_title, text_x, title_y, base_font_size=base_title_sz, max_width=max_text_w, font_weight="bold", fill="#111111")
    )
    # Subtext 1
    svg_parts.append(
        render_keepout_text(sub1, text_x, sub1_y, base_font_size=base_sub_sz, max_width=max_text_w, font_weight="normal", fill="#444444")
    )
    # Subtext 2 (or Bin ID if present)
    sub2_display = sub2
    if spec.bin_id:
        sub2_display = f"{sub2} • {spec.bin_id}" if sub2 else spec.bin_id

    svg_parts.append(
        render_keepout_text(sub2_display, text_x, sub2_y, base_font_size=base_sub_sz, max_width=max_text_w, font_weight="bold", fill=color)
    )

    svg_parts.append('</g>')
    svg_parts.append("</g>")
    return "\n".join(svg_parts)
