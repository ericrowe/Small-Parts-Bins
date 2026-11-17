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

from hardware.labels.vector_icons import (
    get_component_icon_svg,
    get_drive_icon_svg,
    get_head_icon_svg,
    get_label_b_part_illustration_svg,
)

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
        if not self.qr_payload:
            if self.bin_id:
                bin_4d = format_four_digit_bin(self.bin_id, fallback_num=1)
                self.qr_payload = f"HTTP://TASKER-PI.LOCAL:8090/{bin_4d}"
            elif self.part_id:
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
        od_list = format_washer_od_tokens(spec.length, is_sae=bool(spec.size) and not spec.size.upper().startswith("M"))
        title = f"{spec.size} WASHER".strip()
        sub1 = ", ".join(od_list) if od_list else (spec.extra_note or "")
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


# Vertical Split-Label Geometry for Horizontal Drawer Cartridges (mm, Zero Bleed)
VERT_LABEL_W = 11.00
VERT_LABEL_H = 34.00


def format_four_digit_bin(raw_bin: str, fallback_num: int = 1) -> str:
    """Normalize a bin identifier ('BIN-001', 'BIN-0001', '1', '0001') into a 4-digit string ('0001')."""
    if raw_bin:
        m = re.search(r"(\d+)", str(raw_bin))
        if m:
            return f"{int(m.group(1)):04d}"
    return f"{max(1, int(fallback_num)):04d}"


def format_bare_length(raw_length: str) -> str:
    """Strip 'mm' units and prefixes from length strings so metric lengths display as bare numbers (e.g. '6')."""
    if not raw_length:
        return ""
    cleaned = re.sub(r"(?i)\bL:\s*", "", str(raw_length)).strip()
    cleaned = re.sub(r"(?i)\s*mm\b", "", cleaned).strip()
    return cleaned


def format_washer_od_tokens(raw_length: str, is_sae: bool = False) -> list[str]:
    """
    Parse known washer Outer Diameter (OD) values from `raw_length` and format metric ODs
    with explicit 'mm' units (e.g. '9mm', '20mm'). Unknown/blank ODs return an empty list.
    """
    if not raw_length:
        return []
    tokens: list[str] = []
    for part in re.split(r"[,;]+", str(raw_length)):
        cleaned = re.sub(r"(?i)\b(?:L|OD):\s*", "", part).strip()
        cleaned = re.sub(r"(?i)\b(?:washer|fender|flat|split)\b", "", cleaned).strip()
        if not cleaned or cleaned in ("—", "-", "?", "unknown", "none"):
            continue
        bare_num = re.sub(r"(?i)\s*mm\b", "", cleaned).strip()
        try:
            fval = float(bare_num)
            if fval <= 0:
                continue
            num_str = str(int(fval)) if fval.is_integer() else f"{fval:g}"
            tok_fmt = f'{num_str}"' if is_sae else f"{num_str}mm"
        except ValueError:
            tok_fmt = bare_num if is_sae else (cleaned if cleaned.lower().endswith("mm") else f"{bare_num}mm")
        if tok_fmt not in tokens:
            tokens.append(tok_fmt)
    return tokens


def _contrast_text_color_for_bar(hex_color: str) -> str:
    """Return high-contrast text color (#FFFFFF or #111111) for text overlaid on the category color bar."""
    c = (hex_color or "#0077CC").lstrip("#")
    if len(c) == 6:
        try:
            r = int(c[0:2], 16)
            g = int(c[2:4], 16)
            b = int(c[4:6], 16)
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            return "#111111" if lum > 165 else "#FFFFFF"
        except ValueError:
            pass
    return "#FFFFFF"


def _estimate_svg_text_width(text: str, font_size: float, font_weight: str = "bold") -> float:
    """Estimate rendered width in mm for Arial/Helvetica SVG text, accounting for wide glyphs (W, M, m, uppercase)."""
    is_bold = font_weight == "bold"
    total_em = 0.0
    for ch in text:
        if ch in ("W", "M", "m", "@", "%", "×"):
            total_em += 0.94 if is_bold else 0.86
        elif ch.isupper():
            total_em += 0.73 if is_bold else 0.66
        elif ch.isdigit():
            total_em += 0.58 if is_bold else 0.54
        elif ch in (" ", ".", ",", ":", ";", "!", "|", "i", "l", "I", "1", "/", "-"):
            total_em += 0.35 if is_bold else 0.32
        else:
            total_em += 0.58 if is_bold else 0.52
    return total_em * font_size


def render_keepout_centered_text(
    text: str,
    cx: float,
    y: float,
    base_font_size: float,
    max_width: float,
    font_weight: str = "bold",
    fill: str = "#111111",
) -> str:
    """Render horizontally centered SVG text with automatic font scaling keepout protection."""
    if not text:
        return ""
    escaped = escape_xml(text)
    est_width = _estimate_svg_text_width(text, base_font_size, font_weight)
    font_size = base_font_size
    text_length_attr = ""

    if est_width > max_width and max_width > 0:
        scale = max_width / est_width
        font_size = max(base_font_size * scale, base_font_size * 0.55)
        new_est = _estimate_svg_text_width(text, font_size, font_weight)
        if new_est > max_width * 1.01:
            text_length_attr = f' textLength="{max_width:.2f}" lengthAdjust="spacingAndGlyphs"'

    return (
        f'<text x="{cx:.2f}" y="{y:.2f}" text-anchor="middle" '
        f'font-family="Arial, Helvetica, sans-serif" font-weight="{font_weight}" '
        f'font-size="{font_size:.2f}" fill="{fill}"{text_length_attr}>{escaped}</text>'
    )


def render_vertical_split_label_pair_svg(
    spec: LabelData,
    x: float = 0.0,
    y: float = 0.0,
    label_w: float = VERT_LABEL_W,
    label_h: float = VERT_LABEL_H,
    forwarding_base_url: str = "HTTP://TASKER-PI.LOCAL:8090",
    fallback_bin_num: int = 1,
    include_bleed: bool = False,
    bleed: float = BLEED,
    pair_gap_x: float = 0.0,
    include_qr: bool = True,
) -> str:
    """
    Render a vertical split-label pair ([Label A | Label B], each 11x34 mm) for a horizontally
    oriented drawer cartridge:
      - Label A (11x34 mm, Part Identity End):
          * Category color bar at top (Blue = Metric, Orange = SAE) with thread size overlaid.
          * Bare length number or vertical column below color bar (or NUT / WASHER).
          * Optional small Green strip across the bottom for Green nut/washer bins.
      - Label B (11x34 mm, Part Illustration, QR & Bin End):
          * Matching category color bar at top.
          * Part illustration in the middle zone.
          * Low-density QR code encoding `<forwarding_base_url>/<4-digit-id>` + subtle gray 4-digit bin below QR.
      - When `include_bleed=True` (Cricut Print-Then-Cut mode), background and top/bottom color bars
        extend by `bleed` (+1.0 mm) past the cut lines so the finished Cricut-cut labels are identical
        to the paper-cutter labels.
    """
    color = spec.accent_color or "#0077CC"
    bg = spec.bg_color or "#FFFFFF"
    bin_4digit = format_four_digit_bin(spec.bin_id, fallback_num=fallback_bin_num)
    bare_len = format_bare_length(spec.length)
    size_text = (spec.size or spec.name or "").strip()

    comp_lower = (spec.comp_type or "").lower()
    head_lower = (spec.head or "").lower()
    is_nut = comp_lower in ("nut", "nyloc") or head_lower in ("nut", "nyloc", "flange_nut", "square_nut", "wing_nut", "tnut", "tnut_pre", "tnut_post")
    is_washer = comp_lower in ("washer", "split") or head_lower in ("washer", "fender_washer", "split_washer")

    # Two-color convention for Green bins (Nuts & Washers):
    # Top color bar indicates thread system (Blue #0077CC = Metric, Orange #E65100 = SAE/Imperial),
    # and a small Green (#2E7D32) strip across the bottom of Label A indicates the Green bin.
    is_sae_size = bool(size_text) and not size_text.upper().startswith("M")
    if is_nut or is_washer:
        if color.upper() == "#2E7D32":
            top_bar_color = "#E65100" if is_sae_size else "#0077CC"
        else:
            top_bar_color = color
        bottom_strip_color = "#2E7D32"
    else:
        top_bar_color = color
        bottom_strip_color = ""

    bar_text_color = _contrast_text_color_for_bar(top_bar_color)

    pair_id = clean_id("vsplit", spec.part_id or size_text, bin_4digit, int(x), int(y))
    bx = label_w + pair_gap_x
    cx_a = label_w / 2.0
    cx_b = bx + (label_w / 2.0)
    max_txt_w = label_w - 1.6
    b_pad = bleed if include_bleed else 0.0

    svg_parts = [f'<g id="{pair_id}" transform="translate({x:.2f},{y:.2f})">']

    # ==========================================================================
    # LABEL A: Part Identity End (0 .. label_w, 0 .. label_h)
    # ==========================================================================
    bar_a_h = 9.00
    stroke_attr = 'stroke="none"' if include_bleed else 'stroke="#CCCCCC" stroke-width="0.18"'
    svg_parts.append(
        f'<rect x="{-b_pad:.2f}" y="{-b_pad:.2f}" width="{label_w + 2 * b_pad:.2f}" height="{label_h + 2 * b_pad:.2f}" fill="{bg}" {stroke_attr}/>'
    )
    svg_parts.append(
        f'<rect x="{-b_pad:.2f}" y="{-b_pad:.2f}" width="{label_w + 2 * b_pad:.2f}" height="{bar_a_h + b_pad:.2f}" fill="{top_bar_color}" stroke="none"/>'
    )
    if bottom_strip_color:
        bot_strip_h = 2.60
        svg_parts.append(
            f'<rect x="{-b_pad:.2f}" y="{label_h - bot_strip_h:.2f}" width="{label_w + 2 * b_pad:.2f}" height="{bot_strip_h + b_pad:.2f}" fill="{bottom_strip_color}" stroke="none"/>'
        )
    # Size overlaid on the color bar (e.g. "M4")
    if size_text:
        svg_parts.append(
            render_keepout_centered_text(
                size_text,
                cx=cx_a,
                y=6.25,
                base_font_size=4.60,
                max_width=label_w - 1.2,
                font_weight="bold",
                fill=bar_text_color,
            )
        )

    # Bare length / OD below the color bar (e.g. "6", stacked column "6 / 8 / 10", or "NUT"/"WASHER" when length is blank)

    # Resolve optional lower note first so multi-length column layout can adapt cleanly
    note_text = (spec.extra_note or "").strip()
    if note_text.upper() == "PRE-INS":
        note_text = "PRE"
    elif note_text.upper() == "POST-INS":
        note_text = "POST"
    if not note_text:
        if head_lower == "tnut_pre":
            note_text = "PRE"
        elif head_lower == "tnut_post":
            note_text = "POST"

    if is_washer:
        od_tokens = format_washer_od_tokens(spec.length, is_sae=is_sae_size)
        washer_y = 14.00 if (od_tokens or note_text) else 15.80
        svg_parts.append(
            render_keepout_centered_text(
                "WASHER",
                cx=cx_a,
                y=washer_y,
                base_font_size=1.98,
                max_width=label_w - 2.2,
                font_weight="bold",
                fill="#111111",
            )
        )
        if od_tokens:
            if len(od_tokens) == 1:
                y_positions = [20.20] if note_text else [21.40]
                od_fs = 2.40 if note_text else 2.55
            elif len(od_tokens) == 2:
                y_positions = [18.60, 22.20] if note_text else [19.60, 24.40]
                od_fs = 2.30 if note_text else 2.45
            elif len(od_tokens) == 3:
                y_positions = [17.80, 20.60, 23.40] if note_text else [18.80, 22.80, 26.80]
                od_fs = 2.15 if note_text else 2.30
            else:
                y_start = 17.60 if note_text else 18.40
                y_end = 23.40 if note_text else 27.80
                step = (y_end - y_start) / max(1, len(od_tokens) - 1)
                y_positions = [y_start + i * step for i in range(len(od_tokens))]
                od_fs = 1.95 if note_text else 2.10

            for od_val, y_pos in zip(od_tokens, y_positions):
                svg_parts.append(
                    render_keepout_centered_text(
                        od_val,
                        cx=cx_a,
                        y=y_pos,
                        base_font_size=od_fs,
                        max_width=label_w - 2.2,
                        font_weight="bold",
                        fill="#111111",
                    )
                )
    elif bare_len:
        len_parts = [p.strip() for p in re.split(r"[,;]+", bare_len) if p.strip()]
        if len(len_parts) >= 2:
            if len(len_parts) == 2:
                y_positions = [14.30, 19.40] if note_text else [15.80, 22.60]
                col_fs = 3.70 if note_text else 4.40
            elif len(len_parts) == 3:
                y_positions = [13.40, 17.40, 21.40] if note_text else [14.80, 21.00, 27.20]
                col_fs = 3.20 if note_text else 4.20
            else:
                y_start = 13.20 if note_text else 14.00
                y_end = 21.60 if note_text else 29.40
                step = (y_end - y_start) / max(1, len(len_parts) - 1)
                y_positions = [y_start + i * step for i in range(len(len_parts))]
                col_fs = 2.70 if note_text else 3.30

            for part_val, y_pos in zip(len_parts, y_positions):
                svg_parts.append(
                    render_keepout_centered_text(
                        part_val,
                        cx=cx_a,
                        y=y_pos,
                        base_font_size=col_fs,
                        max_width=max_txt_w,
                        font_weight="bold",
                        fill="#111111",
                    )
                )
        else:
            len_fs = 2.50 if ("/" in bare_len or len(bare_len) >= 5) else 4.60
            svg_parts.append(
                render_keepout_centered_text(
                    bare_len,
                    cx=cx_a,
                    y=16.00,
                    base_font_size=len_fs,
                    max_width=max_txt_w,
                    font_weight="bold",
                    fill="#111111",
                )
            )
    elif is_nut:
        if head_lower == "square_nut":
            svg_parts.append(
                render_keepout_centered_text(
                    "SQUARE",
                    cx=cx_a,
                    y=14.60,
                    base_font_size=2.15,
                    max_width=label_w - 2.0,
                    font_weight="bold",
                    fill="#111111",
                )
            )
            svg_parts.append(
                render_keepout_centered_text(
                    "NUT",
                    cx=cx_a,
                    y=17.80,
                    base_font_size=2.40,
                    max_width=label_w - 2.0,
                    font_weight="bold",
                    fill="#111111",
                )
            )
        else:
            nut_word = "NYLOC" if head_lower == "nyloc" else "T-NUT" if head_lower in ("tnut", "tnut_pre", "tnut_post") else "NUT"
            nut_fs = 2.55 if len(nut_word) >= 5 else 3.20
            svg_parts.append(
                render_keepout_centered_text(
                    nut_word,
                    cx=cx_a,
                    y=15.80,
                    base_font_size=nut_fs,
                    max_width=label_w - 2.2,
                    font_weight="bold",
                    fill="#111111",
                )
            )

    if note_text:
        words = note_text.split()
        if len(words) >= 2 and len(note_text) > 8:
            mid = len(words) // 2
            line1 = " ".join(words[:mid])
            line2 = " ".join(words[mid:])
            svg_parts.append(
                render_keepout_centered_text(
                    line1, cx=cx_a, y=24.80, base_font_size=2.05, max_width=max_txt_w, font_weight="bold", fill="#333333"
                )
            )
            svg_parts.append(
                render_keepout_centered_text(
                    line2, cx=cx_a, y=27.60, base_font_size=2.05, max_width=max_txt_w, font_weight="bold", fill="#333333"
                )
            )
        else:
            svg_parts.append(
                render_keepout_centered_text(
                    note_text, cx=cx_a, y=26.00, base_font_size=2.15, max_width=max_txt_w, font_weight="bold", fill="#333333"
                )
            )

    # ==========================================================================
    # LABEL B: Part Illustration & Low-Density QR End (bx .. bx + label_w, 0 .. label_h)
    # ==========================================================================
    bar_b_h = 5.50
    svg_parts.append(
        f'<rect x="{bx - b_pad:.2f}" y="{-b_pad:.2f}" width="{label_w + 2 * b_pad:.2f}" height="{label_h + 2 * b_pad:.2f}" fill="{bg}" {stroke_attr}/>'
    )
    svg_parts.append(
        f'<rect x="{bx - b_pad:.2f}" y="{-b_pad:.2f}" width="{label_w + 2 * b_pad:.2f}" height="{bar_b_h + b_pad:.2f}" fill="{top_bar_color}" stroke="none"/>'
    )

    # Low-density QR code encoding uppercase forwarding URL (Version 1/2 <= 25x25 modules)
    qr_payload = f"{forwarding_base_url.rstrip('/')}/{bin_4digit}".upper()
    qr_sz = min(10.60, label_w - 1.40)
    qr_x = bx + (label_w - qr_sz) / 2.0
    qr_y = label_h - qr_sz - 2.20

    # Fill the space between the top color bar (5.50mm) and the QR code with the part illustration
    avail_top = bar_b_h + 1.00
    avail_bot = qr_y - 1.00
    illus_h = max(8.0, avail_bot - avail_top)
    illus_w = label_w - 2.00
    illus_x = bx + 1.00
    illus_y = avail_top
    svg_parts.append(
        get_label_b_part_illustration_svg(
            comp_type=spec.comp_type,
            head=spec.head,
            x=illus_x,
            y=illus_y,
            w=illus_w,
            h=illus_h,
            color="#111111",
        )
    )

    if include_qr:
        svg_parts.append(generate_qr_svg_path(qr_payload, size=qr_sz, x=qr_x, y=qr_y, color="#111111"))

    # Subtle 4-digit bin number below the QR code in gray text inside the existing 2.20mm bottom margin
    svg_parts.append(
        render_keepout_centered_text(
            bin_4digit,
            cx=cx_b,
            y=label_h - 0.55,
            base_font_size=1.55,
            max_width=label_w - 1.40,
            font_weight="normal",
            fill="#888888",
        )
    )

    svg_parts.append("</g>")
    return "\n".join(svg_parts)


def generate_split_vertical_sheet_svg(
    labels: list[LabelData],
    title: str = "Cartridge Split Labels (11x34mm Zero-Bleed)",
    forwarding_base_url: str = "HTTP://TASKER-PI.LOCAL:8090",
) -> str:
    """
    Compose a zero-bleed Letter sheet (215.9 x 279.4 mm) of vertical 11x34mm [Label A | Label B]
    cartridge pairs (22x34mm per pair) with shared cut edges for fast straight-line paper cutter slicing.
    """
    page_w = 215.90
    page_h = 279.40
    pair_w = VERT_LABEL_W * 2.0  # 22.0 mm
    pair_h = VERT_LABEL_H        # 34.0 mm

    pair_cols = 8  # 8 pairs = 16 labels across (176.0 mm width)
    rows = 7       # 7 rows = 238.0 mm height (56 cartridge pairs = 112 labels per sheet)
    capacity = pair_cols * rows

    grid_w = pair_cols * pair_w
    grid_h = rows * pair_h
    start_x = (page_w - grid_w) / 2.0
    start_y = 18.00

    batch = labels[:capacity]
    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{page_w:.2f}mm" height="{page_h:.2f}mm" viewBox="0 0 {page_w:.2f} {page_h:.2f}">',
        f'  <rect x="0" y="0" width="{page_w:.2f}" height="{page_h:.2f}" fill="#FFFFFF"/>',
        f'  <text x="{start_x:.2f}" y="11.50" font-family="Arial, Helvetica, sans-serif" font-size="3.80" font-weight="bold" fill="#111111">{escape_xml(title)}</text>',
        f'  <text x="{start_x + grid_w:.2f}" y="11.50" text-anchor="end" font-family="Arial, Helvetica, sans-serif" font-size="2.60" fill="#555555">Zero-Bleed Paper Cutter Grid: 11×34 mm Vertical Pairs ([Label A | Label B])</text>',
        '  <g id="split-vertical-pairs">',
    ]

    for idx, spec in enumerate(batch):
        r = idx // pair_cols
        c = idx % pair_cols
        px = start_x + c * pair_w
        py = start_y + r * pair_h
        svg_lines.append(
            render_vertical_split_label_pair_svg(
                spec,
                x=px,
                y=py,
                forwarding_base_url=forwarding_base_url,
                fallback_bin_num=idx + 1,
            )
        )

    svg_lines.append("  </g>")
    svg_lines.append("</svg>")
    return "\n".join(svg_lines)

