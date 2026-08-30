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
