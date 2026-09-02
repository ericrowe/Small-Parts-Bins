#!/usr/bin/env python3
"""Generate the provisional 3x4, 7U carrier used as a two-tray 14U test stack."""

from __future__ import annotations

import json, math, struct
from dataclasses import dataclass
from pathlib import Path

PITCH = 42.0
GRID_X, GRID_Y = 3, 4
OUTER_X, OUTER_Y = 125.5, 167.5
THROAT_X, THROAT_Y = 120.3, 162.3
HEIGHT_U = 7
ENGAGED_HEIGHT = 49.0
LIP_HEIGHT = 4.4
TOTAL_HEIGHT = 53.4
BASE_HEIGHT = 4.75
FLOOR_TOP = 6.75
WALL_MIN = 2.0
CASSETTE = (39.55, 80.0, 28.0)
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
    # Four continuous 2.6 mm outer walls.
    m.add(box(-hx, -ix, -hy + 0.01, hy - 0.01, FLOOR_TOP - 0.05, ENGAGED_HEIGHT))
    m.add(box(ix, hx, -hy + 0.01, hy - 0.01, FLOOR_TOP - 0.05, ENGAGED_HEIGHT))
    m.add(box(-hx, hx, -hy, -iy, FLOOR_TOP - 0.05, ENGAGED_HEIGHT))
    m.add(box(-hx, hx, iy, hy, FLOOR_TOP - 0.05, ENGAGED_HEIGHT))
    # Negative of the stepped base profile, with a continuous stackable rim.
    xp=[(ix,ENGAGED_HEIGHT-.05),(hx,ENGAGED_HEIGHT-.05),(hx,TOTAL_HEIGHT),(hx-.10,TOTAL_HEIGHT),(ix+.70,51.50),(ix+.70,49.70)]
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
        f.write(b'Gridfinity 3x4 7U carrier v0.1'.ljust(80,b' ')); f.write(struct.pack('<I',len(m.triangles)))
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
        for col in (-1,0,1):
            x=ox+(col*39.95+OUTER_X/2-CASSETTE[0]/2)*sx
            y=oy+((row<0)*80.4+3.55)*sy
            rects.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{CASSETTE[0]*sx:.1f}" height="{CASSETTE[1]*sy:.1f}" rx="4" fill="#9ed5e5" stroke="#174c5b"/>')
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="920" height="520" viewBox="0 0 920 520">
<rect width="100%" height="100%" fill="#f7f4ed"/><text x="25" y="20" font-family="sans-serif" font-size="16" font-weight="bold">3×4 carrier v0.1 — 7U tray / 14U two-tray test</text>
<g transform="translate(0 15)"><rect x="{ox}" y="{oy}" width="{OUTER_X*sx}" height="{OUTER_Y*sy}" rx="9" fill="#ddd8ca" stroke="#222" stroke-width="2"/><rect x="{ox+(OUTER_X-THROAT_X)*sx/2}" y="{oy+(OUTER_Y-THROAT_Y)*sy/2}" width="{THROAT_X*sx}" height="{THROAT_Y*sy}" rx="6" fill="#fff" stroke="#7a7467"/>{''.join(rects)}</g>
<g transform="translate(390 55)"><line x1="0" y1="360" x2="360" y2="360" stroke="#222"/><rect x="20" y="196" width="270" height="164" fill="#d4cdbc" stroke="#222"/><rect x="20" y="32" width="270" height="164" fill="#d4cdbc" stroke="#222"/><rect x="42" y="266" width="226" height="94" fill="#9ed5e5" stroke="#174c5b"/><rect x="42" y="102" width="226" height="94" fill="#9ed5e5" stroke="#174c5b"/><line x1="315" y1="32" x2="315" y2="360" stroke="#a33" stroke-width="2"/><text x="325" y="200" font-family="sans-serif" font-size="14">102.4 mm stack</text><line x1="350" y1="4" x2="350" y2="360" stroke="#26734d"/><text x="665" y="22" font-family="sans-serif" font-size="14" transform="rotate(90 665 22)">111.125 mm drawer ceiling; 8.725 mm nominal clearance</text></g>
<text x="25" y="505" font-family="sans-serif" font-size="13">Print two identical carrier STLs. Cassettes remain 14.25 mm below each stacking engagement plane.</text></svg>'''
    path.write_text(svg)

def main():
    out = Path(__file__).parent / 'build'
    out.mkdir(exist_ok=True)
    tray = build_carrier()
    stack = Mesh()
    stack.add(tray)
    stack.add(tray.moved(ENGAGED_HEIGHT))
    write_stl(out / 'carrier_3x4_7u_v0_1.stl', tray)
    write_stl(out / 'REFERENCE_two_carrier_14u_stack_DO_NOT_PRINT.stl', stack)
    write_preview(out / 'carrier_14u_test_preview_v0_1.svg')
    data = {
        'design': '3x4 carrier 14U physical test',
        'version': '0.1',
        'units': 'mm',
        'print_quantity': {'carrier_3x4_7u_v0_1.stl': 2},
        'gridfinity': {
            'pitch_mm': 42,
            'foot_height_mm': 4.75,
            'height_units_per_carrier': 7,
            'engaged_height_per_carrier_mm': 49,
            'lip_height_mm': 4.4,
            'two_carrier_stack_mm': 102.4,
            'profile_source': 'Gridfinity Rebuilt/OpenSCAD standard dimensions; locally generated and provisional pending print',
        },
        'drawer': {
            'measured_internal_height_mm': DRAWER_HEIGHT,
            'nominal_clearance_above_14u_stack_mm': round(DRAWER_HEIGHT - (14 * 7 + LIP_HEIGHT), 3),
        },
        'cassette_fit': {
            'layout': '3 across x 2 deep',
            'closed_envelope_mm': CASSETTE,
            'array_with_0_4_mm_gaps_mm': [119.45, 160.4],
            'lip_throat_mm': [THROAT_X, THROAT_Y],
            'support_floor_z_mm': FLOOR_TOP,
            'cassette_top_z_mm': FLOOR_TOP + CASSETTE[2],
            'stacking_engagement_plane_z_mm': ENGAGED_HEIGHT,
            'vertical_clearance_below_engagement_plane_mm': ENGAGED_HEIGHT - FLOOR_TOP - CASSETTE[2],
        },
        'files': {
            'carrier_3x4_7u_v0_1.stl': audit(tray),
            'REFERENCE_two_carrier_14u_stack_DO_NOT_PRINT.stl': audit(stack),
        },
        'status': 'provisional; requires physical validation',
    }
    (out / 'manifest_v0_1.json').write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps(data, indent=2))

if __name__ == '__main__':
    main()
