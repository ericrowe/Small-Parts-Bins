#!/usr/bin/env python3
"""Generate the Divider Fit Coupon and Test Cards for Plan 003."""

from __future__ import annotations

import json, math, struct
from dataclasses import dataclass
from pathlib import Path

V = tuple[float, float, float]
T = tuple[V, V, V]

@dataclass
class Mesh:
    triangles: list[T]
    def __init__(self): self.triangles = []
    def tri(self, a: V, b: V, c: V):
        ux, uy, uz = b[0]-a[0], b[1]-a[1], b[2]-a[2]
        vx, vy, vz = c[0]-a[0], c[1]-a[1], c[2]-a[2]
        if (uy*vz-uz*vy)**2+(uz*vx-ux*vz)**2+(ux*vy-uy*vx)**2 > 1e-18:
            self.triangles.append((a, b, c))
    def quad(self, a: V, b: V, c: V, d: V):
        self.tri(a, b, c); self.tri(a, c, d)
    def add(self, other: 'Mesh'):
        self.triangles.extend(other.triangles)

def box(x0, x1, y0, y1, z0, z1):
    m = Mesh()
    m.quad((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)) # bottom (-Z)
    m.quad((x0, y0, z1), (x0, y1, z1), (x1, y1, z1), (x1, y0, z1)) # top (+Z)
    m.quad((x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)) # -X
    m.quad((x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)) # +X
    m.quad((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)) # -Y
    m.quad((x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)) # +Y
    return m

def normal(t: T) -> V:
    a, b, c = t
    u = [b[i]-a[i] for i in range(3)]
    v = [c[i]-a[i] for i in range(3)]
    n = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
    q = math.sqrt(sum(x*x for x in n))
    return tuple(x/q for x in n) if q else (0, 0, 0)

def write_stl(path: Path, m: Mesh, title: str):
    with path.open('wb') as f:
        f.write(title.encode('latin1')[:80].ljust(80, b' '))
        f.write(struct.pack('<I', len(m.triangles)))
        for t in m.triangles:
            norm = normal(t)
            f.write(struct.pack('<12fH', *norm, *(q for v in t for q in v), 0))

def audit(m: Mesh):
    edges = {}
    deg = 0
    finite = True
    for t in m.triangles:
        finite &= all(math.isfinite(q) for v in t for q in v)
        a, b, c = t
        if normal(t) == (0, 0, 0): deg += 1
        for p, q in ((a, b), (b, c), (c, a)):
            k = tuple(sorted((tuple(round(x, 4) for x in p), tuple(round(x, 4) for x in q))))
            edges[k] = edges.get(k, 0) + 1
    return {
        'triangles': len(m.triangles),
        'boundary_edges': sum(v == 1 for v in edges.values()),
        'nonmanifold_edges': sum(v > 2 for v in edges.values()),
        'degenerate_triangles': deg,
        'finite_coordinates': finite
    }

# Main Coupon Constants
BODY_W = 38.60
CAV_W = 34.60
WALL = 2.00
FLOOR_Z = 2.00
COUPON_H = 16.00
COUPON_D = 40.00
SLOT_DEPTH = 0.60
GROOVE_DEPTH = 0.60
OV = 0.05

# 4 Test Stations along Y:
# 1. Y = -12.0 mm: 1.30 mm slot (+0.10 mm nominal clearance on 1.20 mm divider)
# 2. Y =  -4.0 mm: 1.40 mm slot (+0.20 mm nominal clearance)
# 3. Y =  +4.0 mm: 1.50 mm slot (+0.30 mm nominal clearance)
# 4. Y = +12.0 mm: 1.60 mm slot (+0.40 mm nominal clearance)
STATIONS = [
    (-12.0, 1.30, "1.30 mm (+0.10)"),
    ( -4.0, 1.40, "1.40 mm (+0.20)"),
    (  4.0, 1.50, "1.50 mm (+0.30)"),
    ( 12.0, 1.60, "1.60 mm (+0.40)"),
]

def build_coupon():
    m = Mesh()
    hx, hy = BODY_W / 2, COUPON_D / 2
    ix, iy = CAV_W / 2, COUPON_D / 2 - 2.00
    
    # 1. Base floor plate: Z in [0, FLOOR_Z - GROOVE_DEPTH + OV] = [0, 1.45]
    m.add(box(-hx, hx, -hy, hy, 0.00, FLOOR_Z - GROOVE_DEPTH + OV))
    
    # 2. Outer left wall: X in [-hx, -ix - SLOT_DEPTH + OV], Z in [FLOOR_Z - GROOVE_DEPTH, COUPON_H]
    m.add(box(-hx, -ix - SLOT_DEPTH + OV, -hy, hy, FLOOR_Z - GROOVE_DEPTH, COUPON_H))
    
    # 3. Outer right wall: X in [ix + SLOT_DEPTH - OV, hx], Z in [FLOOR_Z - GROOVE_DEPTH, COUPON_H]
    m.add(box(ix + SLOT_DEPTH - OV, hx, -hy, hy, FLOOR_Z - GROOVE_DEPTH, COUPON_H))
    
    # 4. Front end wall: Y in [-hy, -iy + OV]
    m.add(box(-ix - SLOT_DEPTH, ix + SLOT_DEPTH, -hy, -iy + OV, FLOOR_Z - GROOVE_DEPTH, COUPON_H))
    
    # 5. Back end wall: Y in [iy - OV, hy]
    m.add(box(-ix - SLOT_DEPTH, ix + SLOT_DEPTH, iy - OV, hy, FLOOR_Z - GROOVE_DEPTH, COUPON_H))
    
    # 6. Segments between slots
    y_points = [-iy]
    for cy, sw, _ in STATIONS:
        y_points.extend([cy - sw / 2, cy + sw / 2])
    y_points.append(iy)
    
    for idx in range(0, len(y_points) - 1, 2):
        y0, y1 = y_points[idx], y_points[idx + 1]
        # Floor between slots:
        m.add(box(-ix - OV, ix + OV, y0 - OV, y1 + OV, FLOOR_Z - GROOVE_DEPTH, FLOOR_Z))
        # Inner left wall between slots:
        m.add(box(-ix - SLOT_DEPTH - OV, -ix, y0 - OV, y1 + OV, FLOOR_Z - GROOVE_DEPTH, COUPON_H))
        # Inner right wall between slots:
        m.add(box(ix, ix + SLOT_DEPTH + OV, y0 - OV, y1 + OV, FLOOR_Z - GROOVE_DEPTH, COUPON_H))
        
    return m

def build_divider(divider_t: float = 1.20, side_clearance: float = 0.15, bottom_clearance: float = 0.10):
    m = Mesh()
    cav_w = CAV_W
    # Total width with wings:
    total_w = cav_w + 2 * (SLOT_DEPTH - side_clearance) # 34.60 + 2 * 0.45 = 35.50 mm
    div_h = COUPON_H - FLOOR_Z # 14.0 mm
    tongue_h = GROOVE_DEPTH - bottom_clearance # 0.50 mm
    
    # Main divider plate:
    m.add(box(-total_w / 2, total_w / 2, -divider_t / 2, divider_t / 2, 0.00, div_h + tongue_h + OV))
    
    # Finger grip tab on top: 10.0 mm wide x 3.5 mm tall
    tab_w = 10.00
    tab_h = 3.50
    m.add(box(-tab_w / 2, tab_w / 2, -divider_t / 2, divider_t / 2, div_h + tongue_h, div_h + tongue_h + tab_h))
    
    return m

def write_preview_svg(path: Path):
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="420" viewBox="0 0 800 420">
<rect width="100%" height="100%" fill="#fbfaf7"/>
<text x="30" y="32" font-family="sans-serif" font-size="18" font-weight="bold" fill="#1e293b">Plan 003 — Cassette Divider Fit Coupon &amp; Ladder</text>
<text x="30" y="55" font-family="sans-serif" font-size="13" fill="#64748b">4 slot tolerance stations: 1.30 mm, 1.40 mm, 1.50 mm, 1.60 mm | 1.20 mm test divider card</text>

<!-- Top-down view of coupon -->
<g transform="translate(40, 85)">
  <rect x="0" y="0" width="220" height="260" rx="4" fill="#e2e8f0" stroke="#334155" stroke-width="2"/>
  <rect x="15" y="15" width="190" height="230" fill="#ffffff" stroke="#94a3b8" stroke-width="1.5"/>
  
  <!-- Slots -->
  <!-- Station 1 -->
  <rect x="5" y="35" width="210" height="12" fill="#cbd5e1" stroke="#475569"/>
  <text x="110" y="44" font-family="sans-serif" font-size="10" font-weight="bold" fill="#1e293b" text-anchor="middle">Station 1: 1.30 mm (+0.10)</text>
  
  <!-- Station 2 -->
  <rect x="5" y="90" width="210" height="14" fill="#cbd5e1" stroke="#475569"/>
  <text x="110" y="100" font-family="sans-serif" font-size="10" font-weight="bold" fill="#1e293b" text-anchor="middle">Station 2: 1.40 mm (+0.20)</text>
  
  <!-- Station 3 -->
  <rect x="5" y="150" width="210" height="16" fill="#cbd5e1" stroke="#475569"/>
  <text x="110" y="161" font-family="sans-serif" font-size="10" font-weight="bold" fill="#1e293b" text-anchor="middle">Station 3: 1.50 mm (+0.30)</text>
  
  <!-- Station 4 -->
  <rect x="5" y="210" width="210" height="18" fill="#cbd5e1" stroke="#475569"/>
  <text x="110" y="222" font-family="sans-serif" font-size="10" font-weight="bold" fill="#1e293b" text-anchor="middle">Station 4: 1.60 mm (+0.40)</text>
  
  <text x="110" y="280" font-family="sans-serif" font-size="12" fill="#334155" text-anchor="middle">Top-Down Slot Layout</text>
</g>

<!-- Cross-Section and Divider Card View -->
<g transform="translate(320, 85)">
  <!-- Cross section of wall slot -->
  <rect x="0" y="0" width="200" height="180" fill="#f1f5f9" stroke="#94a3b8"/>
  <rect x="15" y="0" width="170" height="155" fill="#ffffff" stroke="#cbd5e1"/>
  <!-- Floor groove -->
  <rect x="10" y="155" width="180" height="10" fill="#e2e8f0" stroke="#64748b"/>
  <!-- Side slot recesses -->
  <rect x="10" y="0" width="5" height="155" fill="#e2e8f0"/>
  <rect x="185" y="0" width="5" height="155" fill="#e2e8f0"/>
  
  <text x="100" y="205" font-family="sans-serif" font-size="12" fill="#334155" text-anchor="middle">Sectional Cavity &amp; Groove</text>
</g>

<!-- Divider Card Preview -->
<g transform="translate(560, 85)">
  <rect x="10" y="25" width="180" height="145" fill="#93c5fd" stroke="#1d4ed8" stroke-width="1.5"/>
  <rect x="65" y="0" width="70" height="25" fill="#93c5fd" stroke="#1d4ed8" stroke-width="1.5" rx="3"/>
  <text x="100" y="16" font-family="sans-serif" font-size="11" font-weight="bold" fill="#1e3a8a" text-anchor="middle">PULL TAB</text>
  <text x="100" y="100" font-family="sans-serif" font-size="13" font-weight="bold" fill="#1e3a8a" text-anchor="middle">1.20 mm Card</text>
  <text x="100" y="120" font-family="sans-serif" font-size="11" fill="#1e40af" text-anchor="middle">35.50 × 17.50 mm</text>
  <text x="100" y="205" font-family="sans-serif" font-size="12" fill="#334155" text-anchor="middle">Removable Divider Card</text>
</g>
</svg>'''
    path.write_text(svg)

def main():
    out = Path(__file__).resolve().parent / 'build'
    out.mkdir(exist_ok=True)
    
    coupon = build_coupon()
    div_12 = build_divider(1.20)
    div_10 = build_divider(1.00)
    div_14 = build_divider(1.40)
    
    write_stl(out / 'divider_slot_coupon.stl', coupon, 'Divider Slot Coupon v0.1')
    write_stl(out / 'divider_card_1_2mm.stl', div_12, 'Divider Card 1.20mm v0.1')
    write_stl(out / 'divider_card_1_0mm.stl', div_10, 'Divider Card 1.00mm v0.1')
    write_stl(out / 'divider_card_1_4mm.stl', div_14, 'Divider Card 1.40mm v0.1')
    
    write_preview_svg(out / 'divider_coupon_preview_v0_1.svg')
    
    c_audit = audit(coupon)
    d12_audit = audit(div_12)
    d10_audit = audit(div_10)
    d14_audit = audit(div_14)
    
    manifest = {
        "design": "Plan 003 Cassette Divider Fit Coupon",
        "version": "0.1",
        "stations": [
            {"station": "1", "y_center_mm": -12.0, "slot_width_mm": 1.30, "nominal_clearance_mm": 0.10},
            {"station": "2", "y_center_mm":  -4.0, "slot_width_mm": 1.40, "nominal_clearance_mm": 0.20},
            {"station": "3", "y_center_mm":   4.0, "slot_width_mm": 1.50, "nominal_clearance_mm": 0.30},
            {"station": "4", "y_center_mm":  12.0, "slot_width_mm": 1.60, "nominal_clearance_mm": 0.40},
        ],
        "test_dividers": [
            {"file": "divider_card_1_2mm.stl", "thickness_mm": 1.20, "width_mm": 35.50, "height_mm": 17.50, "audit": d12_audit},
            {"file": "divider_card_1_0mm.stl", "thickness_mm": 1.00, "width_mm": 35.50, "height_mm": 17.50, "audit": d10_audit},
            {"file": "divider_card_1_4mm.stl", "thickness_mm": 1.40, "width_mm": 35.50, "height_mm": 17.50, "audit": d14_audit},
        ],
        "coupon_audit": c_audit
    }
    
    (out / 'manifest_v0_1.json').write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))

if __name__ == '__main__':
    main()
