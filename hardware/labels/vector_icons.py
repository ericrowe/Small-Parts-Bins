"""Vector Iconography Library for Small Parts Fastener Labels.

Provides crisp, high-contrast SVG vector silhouettes for:
  - Head styles (Socket, Button, Flat, Pan, Truss, Hex, Round)
  - Drive types (Hex/Allen, Torx/Star, Phillips, Slotted, Square)
  - Fastener components (Hex Nut, Nyloc, Flange Nut, Flat Washer, Split Lock, Heat-Set Insert)
"""

from __future__ import annotations


def get_head_icon_svg(head: str, x: float, y: float, w: float, h: float, color: str = "#111111") -> str:
    """Return SVG XML for a fastener head profile silhouette positioned in a bounding box [x, y, w, h]."""
    head = head.lower()
    # Viewbox coordinates 0..24 x 0..24 mapped to [x, y, w, h]:
    transform = f'transform="translate({x:.2f},{y:.2f}) scale({w/24.0:.4f},{h/24.0:.4f})"'

    if head in ("shcs", "socket", "cap"):
        # Cylindrical socket cap with shank:
        paths = f'''<g {transform} fill="{color}">
            <rect x="5" y="2" width="14" height="11" rx="0.8"/>
            <rect x="9.5" y="13" width="5" height="9"/>
            <line x1="8" y1="3" x2="8" y2="12" stroke="#FFFFFF" stroke-width="0.8" opacity="0.6"/>
            <line x1="12" y1="3" x2="12" y2="12" stroke="#FFFFFF" stroke-width="0.8" opacity="0.6"/>
            <line x1="16" y1="3" x2="16" y2="12" stroke="#FFFFFF" stroke-width="0.8" opacity="0.6"/>
        </g>'''
    elif head in ("bhcs", "button"):
        # Smooth rounded dome:
        paths = f'''<g {transform} fill="{color}">
            <path d="M 3,13 C 3,5 21,5 21,13 Z"/>
            <rect x="9.5" y="13" width="5" height="9"/>
        </g>'''
    elif head in ("fhcs", "flat", "countersunk"):
        # Countersunk flat top 90 degree slope:
        paths = f'''<g {transform} fill="{color}">
            <polygon points="3,4 21,4 14.5,13 9.5,13"/>
            <rect x="9.5" y="13" width="5" height="9"/>
        </g>'''
    elif head in ("pan", "panhead"):
        # Pan head:
        paths = f'''<g {transform} fill="{color}">
            <path d="M 4,13 L 4,7 C 4,5 6,4 8,4 L 16,4 C 18,4 20,5 20,7 L 20,13 Z"/>
            <rect x="9.5" y="13" width="5" height="9"/>
        </g>'''
    elif head in ("truss",):
        # Wide low profile truss:
        paths = f'''<g {transform} fill="{color}">
            <path d="M 2,13 C 2,7 22,7 22,13 Z"/>
            <rect x="9.5" y="13" width="5" height="9"/>
        </g>'''
    elif head in ("hex", "hexhead"):
        # Hex head profile with chamfers:
        paths = f'''<g {transform} fill="{color}">
            <polygon points="4,4 20,4 21,6 21,12 20,13 4,13 3,12 3,6"/>
            <rect x="9.5" y="13" width="5" height="9"/>
        </g>'''
    else:
        # Default generic bolt silhouette:
        paths = f'''<g {transform} fill="{color}">
            <rect x="5" y="3" width="14" height="10" rx="1"/>
            <rect x="9.5" y="13" width="5" height="9"/>
        </g>'''
    return paths


def get_drive_icon_svg(drive: str, x: float, y: float, size: float, color: str = "#111111") -> str:
    """Return SVG XML for a drive socket silhouette (Hex, Torx, Phillips, Slotted, Square)."""
    drive = drive.lower()
    transform = f'transform="translate({x:.2f},{y:.2f}) scale({size/24.0:.4f},{size/24.0:.4f})"'

    if drive in ("hex", "allen"):
        # Regular hexagon:
        paths = f'''<g {transform} fill="{color}">
            <polygon points="12,3 19.8,7.5 19.8,16.5 12,21 4.2,16.5 4.2,7.5"/>
        </g>'''
    elif drive in ("torx", "star"):
        # 6-pointed Torx star profile:
        paths = f'''<g {transform} fill="{color}">
            <path d="M 12,2 C 12.8,2 13.5,3.8 14.2,4.8 C 15.2,4.5 16.5,4.7 17.2,5.2 C 17.8,5.7 18.2,7 18.3,8.2 C 19.2,8.7 20.8,9.7 21,10.6 C 21.2,11.5 20.2,12.5 19.7,13.4 C 20.1,14.4 20.2,15.7 19.8,16.5 C 19.4,17.3 18.1,18 17.1,18.4 C 16.7,19.3 15.8,20.8 15,21.2 C 14.1,21.6 13,20.8 12,20.8 C 11,20.8 9.9,21.6 9,21.2 C 8.2,20.8 7.3,19.3 6.9,18.4 C 5.9,18 4.6,17.3 4.2,16.5 C 3.8,15.7 3.9,14.4 4.3,13.4 C 3.8,12.5 2.8,11.5 3,10.6 C 3.2,9.7 4.8,8.7 5.7,8.2 C 5.8,7 6.2,5.7 6.8,5.2 C 7.5,4.7 8.8,4.5 9.8,4.8 C 10.5,3.8 11.2,2 12,2 Z"/>
        </g>'''
    elif drive in ("phillips", "ph"):
        # Cross:
        paths = f'''<g {transform} fill="{color}">
            <path d="M 10,3 L 14,3 L 14,10 L 21,10 L 21,14 L 14,14 L 14,21 L 10,21 L 10,14 L 3,14 L 3,10 L 10,10 Z"/>
        </g>'''
    elif drive in ("slotted", "slot"):
        # Single horizontal slot:
        paths = f'''<g {transform} fill="{color}">
            <circle cx="12" cy="12" r="9" fill="none" stroke="{color}" stroke-width="2"/>
            <rect x="4" y="10" width="16" height="4" rx="0.5"/>
        </g>'''
    elif drive in ("square", "robertson", "sq"):
        # Square:
        paths = f'''<g {transform} fill="{color}">
            <rect x="5.5" y="5.5" width="13" height="13" rx="1"/>
        </g>'''
    else:
        # Default hex:
        paths = f'''<g {transform} fill="{color}">
            <polygon points="12,3 19.8,7.5 19.8,16.5 12,21 4.2,16.5 4.2,7.5"/>
        </g>'''
    return paths


def get_component_icon_svg(comp_type: str, x: float, y: float, w: float, h: float, color: str = "#111111") -> str:
    """Return SVG XML for non-bolt components (Nuts, Washers, Heat-Set Inserts)."""
    comp_type = comp_type.lower()
    transform = f'transform="translate({x:.2f},{y:.2f}) scale({w/24.0:.4f},{h/24.0:.4f})"'

    if "nyloc" in comp_type:
        # Hex nut with top nylon ring:
        paths = f'''<g {transform} fill="{color}">
            <polygon points="3,9 21,9 21,19 3,19"/>
            <path d="M 6,9 C 6,5 18,5 18,9 Z" fill="#0077CC"/>
        </g>'''
    elif "flange" in comp_type:
        # Hex nut with bottom flange:
        paths = f'''<g {transform} fill="{color}">
            <polygon points="5,5 19,5 19,16 5,16"/>
            <rect x="2" y="16" width="20" height="4" rx="0.5"/>
        </g>'''
    elif "nut" in comp_type:
        # Standard hex nut:
        paths = f'''<g {transform} fill="{color}">
            <polygon points="3,6 21,6 21,18 3,18"/>
            <line x1="9" y1="6" x2="9" y2="18" stroke="#FFFFFF" stroke-width="0.8" opacity="0.6"/>
            <line x1="15" y1="6" x2="15" y2="18" stroke="#FFFFFF" stroke-width="0.8" opacity="0.6"/>
        </g>'''
    elif "split" in comp_type or "lock" in comp_type:
        # Split spring washer:
        paths = f'''<g {transform} fill="none" stroke="{color}" stroke-width="3">
            <path d="M 5,14 A 8,8 0 1,1 19,10"/>
        </g>'''
    elif "washer" in comp_type:
        # Flat washer (annulus):
        paths = f'''<g {transform} fill="{color}">
            <circle cx="12" cy="12" r="9"/>
            <circle cx="12" cy="12" r="4.5" fill="#FFFFFF"/>
        </g>'''
    elif "insert" in comp_type or "heatset" in comp_type:
        # Brass knurled heat-set insert:
        paths = f'''<g {transform} fill="#C5A059">
            <rect x="5" y="3" width="14" height="18" rx="1"/>
            <line x1="5" y1="7" x2="19" y2="7" stroke="#8A6D3B" stroke-width="1"/>
            <line x1="5" y1="12" x2="19" y2="12" stroke="#8A6D3B" stroke-width="1.2"/>
            <line x1="5" y1="17" x2="19" y2="17" stroke="#8A6D3B" stroke-width="1"/>
            <line x1="7" y1="3" x2="17" y2="12" stroke="#8A6D3B" stroke-width="0.8" opacity="0.6"/>
            <line x1="17" y1="12" x2="7" y2="21" stroke="#8A6D3B" stroke-width="0.8" opacity="0.6"/>
        </g>'''
    else:
        paths = f'''<g {transform} fill="{color}">
            <circle cx="12" cy="12" r="8"/>
        </g>'''
    return paths


def get_label_b_part_illustration_svg(
    comp_type: str,
    head: str,
    x: float,
    y: float,
    w: float,
    h: float,
    color: str = "#111111",
) -> str:
    """
    Render a bold, high-contrast vector illustration of the part for Label B (the 12x35mm QR label),
    filling the space between the top category color bar and the bottom QR code.
      - All bolts/screws use a single unmistakable generic threaded bolt illustration.
      - Standard hex nuts use a hex nut illustration.
      - Specialty nuts (Nyloc lock nut, Flange nut, Square nut, Pre-Insert T-Nut, Post-Insert T-Nut),
        washers (Flat, Fender, Split Lock), and Heat-Set Inserts each have a distinct illustration.
     Coordinates are authored in a 100x100 viewBox and scaled uniformly into [x, y, w, h].
    """
    c_type = (comp_type or "bolt").strip().lower()
    h_type = (head or "shcs").strip().lower()

    side = min(w, h)
    ox = x + (w - side) / 2.0
    oy = y + (h - side) / 2.0
    scale = side / 100.0
    transform = f'transform="translate({ox:.2f},{oy:.2f}) scale({scale:.4f})"'

    # 1. Pre-Insert T-Nut (Top-down rectangular body with a clean circular hole in the center)
    if h_type in ("tnut_pre", "tnut"):
        return f'''<g class="part-illustration-tnut-pre" {transform}>
            <rect x="8" y="24" width="84" height="52" rx="5" fill="{color}"/>
            <circle cx="50" cy="50" r="15" fill="#FFFFFF"/>
        </g>'''

    # 2. Post-Insert T-Nut (Drop-in / Hammer-head cam profile with diagonal locking corners + central tapped hole)
    if h_type == "tnut_post":
        return f'''<g class="part-illustration-tnut-post" {transform}>
            <polygon points="34,14 82,14 90,22 90,46 66,86 18,86 10,78 10,54" fill="{color}"/>
            <polygon points="37,22 76,22 81,27 81,44 63,78 24,78 19,73 19,56"
                     fill="none" stroke="#FFFFFF" stroke-width="2.4" opacity="0.65"/>
            <circle cx="50" cy="50" r="20" fill="#FFFFFF"/>
            <circle cx="50" cy="50" r="15" fill="none" stroke="{color}" stroke-width="2.8" stroke-dasharray="6,3"/>
        </g>'''

    # 3. Nyloc Lock Nut (Hex base + raised rounded nylon locking collar dome at top)
    if h_type == "nyloc" or c_type == "nyloc":
        return f'''<g class="part-illustration-nyloc" {transform}>
            <rect x="20" y="14" width="60" height="34" rx="14" fill="#FFFFFF" stroke="{color}" stroke-width="5"/>
            <rect x="27" y="21" width="46" height="14" rx="5" fill="#0077CC"/>
            <polygon points="10,44 90,44 90,82 82,88 18,88 10,82" fill="{color}"/>
            <line x1="34" y1="44" x2="34" y2="88" stroke="#FFFFFF" stroke-width="3"/>
            <line x1="66" y1="44" x2="66" y2="88" stroke="#FFFFFF" stroke-width="3"/>
            <line x1="38" y1="15" x2="38" y2="44" stroke="{color}" stroke-width="2.2" stroke-dasharray="3,3"/>
            <line x1="62" y1="15" x2="62" y2="44" stroke="{color}" stroke-width="2.2" stroke-dasharray="3,3"/>
        </g>'''

    # 4. Flange / Serrated Nut (Hex body + wide flared serrated base flange)
    if h_type == "flange_nut":
        return f'''<g class="part-illustration-flange-nut" {transform}>
            <polygon points="20,20 80,20 84,26 84,66 16,66 16,26" fill="{color}"/>
            <line x1="38" y1="20" x2="38" y2="66" stroke="#FFFFFF" stroke-width="3"/>
            <line x1="62" y1="20" x2="62" y2="66" stroke="#FFFFFF" stroke-width="3"/>
            <polygon points="16,66 84,66 94,76 94,85 6,85 6,76" fill="{color}"/>
            <line x1="14" y1="66" x2="86" y2="66" stroke="#FFFFFF" stroke-width="2.2"/>
            <line x1="16" y1="85" x2="12" y2="91" stroke="{color}" stroke-width="3"/>
            <line x1="28" y1="85" x2="24" y2="91" stroke="{color}" stroke-width="3"/>
            <line x1="40" y1="85" x2="36" y2="91" stroke="{color}" stroke-width="3"/>
            <line x1="52" y1="85" x2="48" y2="91" stroke="{color}" stroke-width="3"/>
            <line x1="64" y1="85" x2="60" y2="91" stroke="{color}" stroke-width="3"/>
            <line x1="76" y1="85" x2="72" y2="91" stroke="{color}" stroke-width="3"/>
            <line x1="88" y1="85" x2="84" y2="91" stroke="{color}" stroke-width="3"/>
        </g>'''

    # 5. Square Nut (Top-down 1:1 square with a clean circular hole in the center)
    if h_type == "square_nut":
        return f'''<g class="part-illustration-square-nut" {transform}>
            <rect x="15" y="15" width="70" height="70" rx="5" fill="{color}"/>
            <circle cx="50" cy="50" r="20" fill="#FFFFFF"/>
        </g>'''

    # 6. Standard Hex Nut (Top-down hexagon with chamfer ring + threaded center bore)
    if c_type == "nut" or h_type in ("nut", "wing_nut"):
        return f'''<g class="part-illustration-hex-nut" {transform}>
            <polygon points="50,7 89,28.5 89,71.5 50,93 11,71.5 11,28.5" fill="{color}"/>
            <circle cx="50" cy="50" r="34" fill="none" stroke="#FFFFFF" stroke-width="2.2" opacity="0.65"/>
            <circle cx="50" cy="50" r="21" fill="#FFFFFF"/>
            <circle cx="50" cy="50" r="16" fill="none" stroke="{color}" stroke-width="2.8" stroke-dasharray="6.5,3.2"/>
        </g>'''

    # 7. Split Lock Washer (Helical split ring with offset gap cut at top)
    if h_type == "split_washer" or c_type == "split":
        return f'''<g class="part-illustration-split-washer" {transform}>
            <circle cx="50" cy="52" r="40" fill="{color}"/>
            <circle cx="50" cy="52" r="21" fill="#FFFFFF"/>
            <polygon points="42,6 60,6 56,34 45,34" fill="#FFFFFF"/>
            <line x1="42" y1="10" x2="45" y2="32" stroke="{color}" stroke-width="3.5" stroke-linecap="round"/>
            <line x1="60" y1="15" x2="55" y2="33" stroke="{color}" stroke-width="3.5" stroke-linecap="round"/>
        </g>'''

    # 8. Fender Washer (Extra-wide OD with small inner hole)
    if h_type == "fender_washer":
        return f'''<g class="part-illustration-fender-washer" {transform}>
            <circle cx="50" cy="50" r="43" fill="{color}"/>
            <circle cx="50" cy="50" r="37" fill="none" stroke="#FFFFFF" stroke-width="1.8" opacity="0.45"/>
            <circle cx="50" cy="50" r="13" fill="#FFFFFF"/>
            <circle cx="50" cy="50" r="13" fill="none" stroke="{color}" stroke-width="2"/>
        </g>'''

    # 9. Standard Flat Washer (Classic concentric washer ring)
    if c_type == "washer" or h_type == "washer":
        return f'''<g class="part-illustration-flat-washer" {transform}>
            <circle cx="50" cy="50" r="41" fill="{color}"/>
            <circle cx="50" cy="50" r="21" fill="#FFFFFF"/>
        </g>'''

    # 10. Brass Heat-Set Insert (Stepped cylinder with opposing diagonal knurl bands)
    if c_type == "insert" or h_type == "insert":
        return f'''<g class="part-illustration-insert" {transform}>
            <rect x="20" y="10" width="60" height="28" rx="3" fill="{color}"/>
            <line x1="28" y1="13" x2="36" y2="35" stroke="#FFFFFF" stroke-width="2.5"/>
            <line x1="41" y1="13" x2="49" y2="35" stroke="#FFFFFF" stroke-width="2.5"/>
            <line x1="54" y1="13" x2="62" y2="35" stroke="#FFFFFF" stroke-width="2.5"/>
            <line x1="67" y1="13" x2="74" y2="35" stroke="#FFFFFF" stroke-width="2.5"/>
            <rect x="27" y="38" width="46" height="10" fill="{color}"/>
            <rect x="20" y="48" width="60" height="26" rx="3" fill="{color}"/>
            <line x1="36" y1="51" x2="28" y2="71" stroke="#FFFFFF" stroke-width="2.5"/>
            <line x1="49" y1="51" x2="41" y2="71" stroke="#FFFFFF" stroke-width="2.5"/>
            <line x1="62" y1="51" x2="54" y2="71" stroke="#FFFFFF" stroke-width="2.5"/>
            <line x1="74" y1="51" x2="67" y2="71" stroke="#FFFFFF" stroke-width="2.5"/>
            <rect x="27" y="74" width="46" height="16" rx="2" fill="{color}"/>
            <ellipse cx="50" cy="14" rx="16" ry="3.5" fill="#FFFFFF"/>
        </g>'''

    # 11. Generic Bolt (Used for ALL bolts & screws regardless of head type — fills vertical height)
    b_scale_x = w / 100.0
    b_scale_y = min(h / 100.0, b_scale_x * 1.32)
    b_ox = x + (w - 100.0 * b_scale_x) / 2.0
    b_oy = y + (h - 100.0 * b_scale_y) / 2.0
    b_transform = f'transform="translate({b_ox:.2f},{b_oy:.2f}) scale({b_scale_x:.4f},{b_scale_y:.4f})"'
    return f'''<g class="part-illustration-bolt" {b_transform}>
        <polygon points="18,6 82,6 86,11 86,25 14,25 14,11" fill="{color}"/>
        <line x1="35" y1="6" x2="35" y2="25" stroke="#FFFFFF" stroke-width="2.8"/>
        <line x1="65" y1="6" x2="65" y2="25" stroke="#FFFFFF" stroke-width="2.8"/>
        <rect x="10" y="25" width="80" height="4.5" rx="1.5" fill="{color}"/>
        <polygon points="32,29.5 68,29.5 68,89 61,96 39,96 32,89" fill="{color}"/>
        <line x1="32" y1="39" x2="68" y2="35" stroke="#FFFFFF" stroke-width="2.5"/>
        <line x1="32" y1="48" x2="68" y2="44" stroke="#FFFFFF" stroke-width="2.5"/>
        <line x1="32" y1="57" x2="68" y2="53" stroke="#FFFFFF" stroke-width="2.5"/>
        <line x1="32" y1="66" x2="68" y2="62" stroke="#FFFFFF" stroke-width="2.5"/>
        <line x1="32" y1="75" x2="68" y2="71" stroke="#FFFFFF" stroke-width="2.5"/>
        <line x1="32" y1="84" x2="68" y2="80" stroke="#FFFFFF" stroke-width="2.5"/>
    </g>'''

