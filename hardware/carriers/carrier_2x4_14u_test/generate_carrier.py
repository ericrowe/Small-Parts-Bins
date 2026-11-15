#!/usr/bin/env python3
"""Generate the 2x4, 7U Gridfinity carrier (4-cassette 2x2 layout) for a two-tray 14U stack."""

from __future__ import annotations

import json, math, struct
from dataclasses import dataclass
from pathlib import Path

PITCH = 42.0
GRID_X, GRID_Y = 2, 4
OUTER_X, OUTER_Y = 83.5, 167.5
THROAT_X, THROAT_Y = 79.9, 162.3
WALL_X = round((OUTER_X - THROAT_X) / 2, 2)  # 1.80 mm (4 perimeters @ 0.45 mm extrusion)
WALL_Y = round((OUTER_Y - THROAT_Y) / 2, 2)  # 2.60 mm
HEIGHT_U = 7
ENGAGED_HEIGHT = 49.0
LIP_HEIGHT = 4.4
TOTAL_HEIGHT = 53.4
BASE_HEIGHT = 4.75
FLOOR_TOP = 6.75
CASSETTE = (39.75, 80.0, 36.4)
CASSETTE_BODY_W = 38.6
GAP = 0.4
DRAWER_HEIGHT = 111.125

V = tuple[float, float, float]
T = tuple[V, V, V]

@dataclass
class Mesh:
    triangles: list[T]
    def __init__(self): self.triangles = []
    def tri(self, a: V, b: V, c: V):
        ux,uy,uz=b[0]-a[0],b[1]-a[1],b[2]-a[2]
        vx,vy,vz=c[0]-a[0],c[1]-a[1],c[2]-a[2]
        if (uy*vz-uz*vy)**2+(uz*vx-ux*vz)**2+(ux*vy-uy*vx)**2 > 1e-18:
            self.triangles.append((a,b,c))
    def quad(self,a:V,b:V,c:V,d:V): self.tri(a,b,c); self.tri(a,c,d)
    def add(self, other:'Mesh'): self.triangles.extend(other.triangles)
    def moved(self,dz:float):
        m=Mesh(); m.triangles=[tuple((x,y,z+dz) for x,y,z in t) for t in self.triangles]; return m

def rounded_rect(w:float,d:float,r:float,n:int=6):
    pts=[]
    for cx,cy,start in ((w/2-r,d/2-r,0),(-w/2+r,d/2-r,90),(-w/2+r,-d/2+r,180),(w/2-r,-d/2+r,270)):
        for i in range(n+1):
            a=math.radians(start+i*90/n); pts.append((cx+r*math.cos(a),cy+r*math.sin(a)))
    return pts

def loft(rings:list[tuple[float,list[tuple[float,float]]]]) -> Mesh:
    m=Mesh(); count=len(rings[0][1])
    for _,p in rings:
        assert len(p)==count
    z,p=rings[0]
    for i in range(1,count-1): m.tri((p[0][0],p[0][1],z),(p[i+1][0],p[i+1][1],z),(p[i][0],p[i][1],z))
    z,p=rings[-1]
    for i in range(1,count-1): m.tri((p[0][0],p[0][1],z),(p[i][0],p[i][1],z),(p[i+1][0],p[i+1][1],z))
    for (z0,p0),(z1,p1) in zip(rings,rings[1:]):
        for i in range(count):
            j=(i+1)%count; m.quad((p0[i][0],p0[i][1],z0),(p0[j][0],p0[j][1],z0),(p1[j][0],p1[j][1],z1),(p1[i][0],p1[i][1],z1))
    return m

def box(x0,x1,y0,y1,z0,z1):
    p=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]; return loft([(z0,p),(z1,p)])

def prism_y(profile:list[tuple[float,float]],y0:float,y1:float):
    m=Mesh(); n=len(profile)
    for i in range(1,n-1):
        m.tri((profile[0][0],y0,profile[0][1]),(profile[i][0],y0,profile[i][1]),(profile[i+1][0],y0,profile[i+1][1]))
        m.tri((profile[0][0],y1,profile[0][1]),(profile[i+1][0],y1,profile[i+1][1]),(profile[i][0],y1,profile[i][1]))
    for i in range(n):
        j=(i+1)%n; m.quad((profile[i][0],y0,profile[i][1]),(profile[i][0],y1,profile[i][1]),(profile[j][0],y1,profile[j][1]),(profile[j][0],y0,profile[j][1]))
    return m

def prism_x(profile:list[tuple[float,float]],x0:float,x1:float):
    m=prism_y(profile,x0,x1)
    return MeshFrom([((y,x,z) for x,y,z in t) for t in m.triangles])

def MeshFrom(tris):
    m=Mesh(); m.triangles=[tuple(t) for t in tris]; return m

def build_carrier():
    m=Mesh()
    # Standard 4.75 mm Gridfinity feet: 35.6 -> 37.2 -> 41.5 mm.
    for ix in range(GRID_X):
        for iy in range(GRID_Y):
            cx=(ix-(GRID_X-1)/2)*PITCH; cy=(iy-(GRID_Y-1)/2)*PITCH
            rings=[]
            for z,w,r in ((0,35.6,3.2),(.8,37.2,3.4),(2.6,37.2,3.4),(4.75,41.5,3.75)):
                rings.append((z,[(x+cx,y+cy) for x,y in rounded_rect(w,w,r)]))
            m.add(loft(rings))
    # Positive overlaps avoid slicer-dependent coplanar contacts between shells.
    m.add(loft([(BASE_HEIGHT-.05,rounded_rect(OUTER_X,OUTER_Y,3.75)),(FLOOR_TOP,rounded_rect(OUTER_X,OUTER_Y,3.75))]))
    hx,hy=OUTER_X/2,OUTER_Y/2; ix,iy=THROAT_X/2,THROAT_Y/2
    # Continuous outer walls: 1.80 mm in X (79.9 mm throat for 2 cassettes), 2.60 mm in Y (162.3 mm throat).
    m.add(box(-hx, -ix, -hy + 0.01, hy - 0.01, FLOOR_TOP - 0.05, ENGAGED_HEIGHT))
    m.add(box(ix, hx, -hy + 0.01, hy - 0.01, FLOOR_TOP - 0.05, ENGAGED_HEIGHT))
    m.add(box(-hx, hx, -hy, -iy, FLOOR_TOP - 0.05, ENGAGED_HEIGHT))
    m.add(box(-hx, hx, iy, hy, FLOOR_TOP - 0.05, ENGAGED_HEIGHT))
    # Negative of the stepped base profile, with a continuous stackable rim.
    xp=[(ix,ENGAGED_HEIGHT-.05),(hx,ENGAGED_HEIGHT-.05),(hx,TOTAL_HEIGHT),(hx-.10,TOTAL_HEIGHT),(ix+.05,51.50),(ix+.05,49.70)]
    xn=[(-x,z) for x,z in reversed(xp)]
    yp=[(iy,ENGAGED_HEIGHT-.05),(hy,ENGAGED_HEIGHT-.05),(hy,TOTAL_HEIGHT),(hy-.10,TOTAL_HEIGHT),(iy+.70,51.50),(iy+.70,49.70)]
    yn=[(-y,z) for y,z in reversed(yp)]
    m.add(prism_y(xp,-hy+.01,hy-.01)); m.add(prism_y(xn,-hy+.01,hy-.01))
    m.add(prism_x(yp,-hx+.01,hx-.01)); m.add(prism_x(yn,-hx+.01,hx-.01))
    return m

def normal(t):
    a,b,c=t; u=[b[i]-a[i] for i in range(3)]; v=[c[i]-a[i] for i in range(3)]
    n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]); q=math.sqrt(sum(x*x for x in n))
    return tuple(x/q for x in n) if q else (0,0,0)

def write_stl(path:Path,m:Mesh):
    with path.open('wb') as f:
        f.write(b'Gridfinity 2x4 7U carrier v0.1'.ljust(80,b' ')); f.write(struct.pack('<I',len(m.triangles)))
        for t in m.triangles: f.write(struct.pack('<12fH',*normal(t),*(q for v in t for q in v),0))

def audit(m:Mesh):
    edges={}; deg=0; finite=True
    for t in m.triangles:
        finite &= all(math.isfinite(q) for v in t for q in v)
        a,b,c=t
        area=normal(t); deg += area==(0,0,0)
        for p,q in ((a,b),(b,c),(c,a)):
            k=tuple(sorted((tuple(round(x,6) for x in p),tuple(round(x,6) for x in q)))); edges[k]=edges.get(k,0)+1
    return {'triangles':len(m.triangles),'boundary_edges':sum(v==1 for v in edges.values()),'nonmanifold_edges':sum(v>2 for v in edges.values()),'degenerate_triangles':deg,'finite_coordinates':finite}

def write_preview(path:Path):
    sx,sy=2.4,2.4; ox,oy=25,25
    rects=[]
    for row in (-1,1):
        for col in (-0.5, 0.5):
            x=ox+(col*39.95+OUTER_X/2-CASSETTE[0]/2)*sx
            y=oy+((row<0)*80.4+3.55)*sy
            rects.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{CASSETTE[0]*sx:.1f}" height="{CASSETTE[1]*sy:.1f}" rx="4" fill="#9ed5e5" stroke="#174c5b"/>')
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="920" height="520" viewBox="0 0 920 520">
<rect width="100%" height="100%" fill="#f7f4ed"/><text x="25" y="20" font-family="sans-serif" font-size="16" font-weight="bold">2×4 carrier v0.1 — 7U tray (4 cassettes) / 14U two-tray stack</text>
<g transform="translate(0 15)"><rect x="{ox}" y="{oy}" width="{OUTER_X*sx}" height="{OUTER_Y*sy}" rx="9" fill="#ddd8ca" stroke="#222" stroke-width="2"/><rect x="{ox+(OUTER_X-THROAT_X)*sx/2}" y="{oy+(OUTER_Y-THROAT_Y)*sy/2}" width="{THROAT_X*sx}" height="{THROAT_Y*sy}" rx="6" fill="#fff" stroke="#7a7467"/>{''.join(rects)}</g>
<g transform="translate(390 55)"><line x1="0" y1="360" x2="360" y2="360" stroke="#222"/><rect x="20" y="196" width="180" height="164" fill="#d4cdbc" stroke="#222"/><rect x="20" y="32" width="180" height="164" fill="#d4cdbc" stroke="#222"/><rect x="35" y="246" width="150" height="114" fill="#9ed5e5" stroke="#174c5b"/><rect x="35" y="82" width="150" height="114" fill="#9ed5e5" stroke="#174c5b"/><line x1="225" y1="32" x2="225" y2="360" stroke="#a33" stroke-width="2"/><text x="235" y="200" font-family="sans-serif" font-size="14">102.4 mm stack</text><line x1="350" y1="4" x2="350" y2="360" stroke="#26734d"/><text x="580" y="22" font-family="sans-serif" font-size="14" transform="rotate(90 580 22)">111.125 mm drawer ceiling; 8.725 mm nominal clearance</text></g>
<text x="25" y="505" font-family="sans-serif" font-size="13">Holds 4 cassettes (2 across × 2 deep). 79.9 × 162.3 mm throat; 1.80 mm X-walls, 2.60 mm Y-walls.</text></svg>'''
    path.write_text(svg)

def main():
    out = Path(__file__).parent / 'build'
    out.mkdir(exist_ok=True)
    tray = build_carrier()
    stack = Mesh()
    stack.add(tray)
    stack.add(tray.moved(ENGAGED_HEIGHT))
    write_stl(out / 'carrier_2x4_7u_v0_1.stl', tray)
    write_stl(out / 'REFERENCE_two_carrier_14u_stack_DO_NOT_PRINT.stl', stack)
    write_preview(out / 'carrier_14u_test_preview_v0_1.svg')
    data = {
        'design': '2x4 carrier 14U physical test',
        'version': '0.1',
        'units': 'mm',
        'print_quantity': {'carrier_2x4_7u_v0_1.stl': 2},
        'gridfinity': {
            'grid_units': [GRID_X, GRID_Y],
            'pitch_mm': 42,
            'outer_dimensions_mm': [OUTER_X, OUTER_Y, TOTAL_HEIGHT],
            'foot_height_mm': 4.75,
            'height_units_per_carrier': 7,
            'engaged_height_per_carrier_mm': 49,
            'lip_height_mm': 4.4,
            'two_carrier_stack_mm': 102.4,
            'wall_thickness_x_mm': WALL_X,
            'wall_thickness_y_mm': WALL_Y,
            'profile_source': 'Gridfinity standard 42 mm pitch; 1.80 mm X-walls and 2.60 mm Y-walls for 2x2 cassette packing',
        },
        'drawer': {
            'measured_internal_height_mm': DRAWER_HEIGHT,
            'nominal_clearance_above_14u_stack_mm': round(DRAWER_HEIGHT - (14 * 7 + LIP_HEIGHT), 3),
        },
        'cassette_fit': {
            'layout': '2 across x 2 deep (4 cassettes)',
            'closed_envelope_mm': CASSETTE,
            'nominal_body_width_mm': CASSETTE_BODY_W,
            'array_max_envelope_mm': [round(2 * CASSETTE[0], 2), round(2 * CASSETTE[1] + GAP, 2)],
            'array_lower_body_mm': [round(2 * CASSETTE_BODY_W, 2), round(2 * CASSETTE[1] + GAP, 2)],
            'lip_throat_mm': [THROAT_X, THROAT_Y],
            'lateral_clearance_at_hinge_knuckles_mm': round(THROAT_X - 2 * CASSETTE[0], 2),
            'lateral_clearance_at_lower_bodies_mm': round(THROAT_X - 2 * CASSETTE_BODY_W, 2),
            'axial_clearance_y_mm': round(THROAT_Y - 2 * CASSETTE[1], 2),
            'support_floor_z_mm': FLOOR_TOP,
            'cassette_top_z_mm': round(FLOOR_TOP + CASSETTE[2], 2),
            'stacking_engagement_plane_z_mm': ENGAGED_HEIGHT,
            'vertical_clearance_below_engagement_plane_mm': round(ENGAGED_HEIGHT - FLOOR_TOP - CASSETTE[2], 2),
        },
        'files': {
            'carrier_2x4_7u_v0_1.stl': audit(tray),
            'REFERENCE_two_carrier_14u_stack_DO_NOT_PRINT.stl': audit(stack),
        },
        'status': 'provisional; ready for overnight physical print validation',
    }
    (out / 'manifest_v0_1.json').write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps(data, indent=2))

if __name__ == '__main__':
    main()
