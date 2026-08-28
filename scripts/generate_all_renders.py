#!/usr/bin/env python3
"""Generate high-resolution 3D renders of all Gridfinity Glass-Window Cassette components."""

from __future__ import annotations

import struct
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from pathlib import Path

def load_stl(path: Path) -> np.ndarray:
    with path.open('rb') as f:
        _ = f.read(80)
        num_tri = struct.unpack('<I', f.read(4))[0]
        data = f.read()
    
    record_dtype = np.dtype([
        ('normal', np.float32, (3,)),
        ('vertices', np.float32, (3, 3)),
        ('attr', np.uint16)
    ])
    arr = np.frombuffer(data, dtype=record_dtype, count=num_tri)
    return arr['vertices']

def render_multiview(stl_path: Path, out_png: Path, title: str, subtitle: str, face_color='#38bdf8', edge_color='#0284c7'):
    verts = load_stl(stl_path)
    
    fig = plt.figure(figsize=(15, 9.5), dpi=220)
    fig.patch.set_facecolor('#f8fafc')
    
    views = [
        ('Isometric 3D View', 28, -45),
        ('Top View (XY)', 90, -90),
        ('Front View (XZ)', 0, -90),
        ('Side View (YZ)', 0, 0),
    ]
    
    all_pts = verts.reshape(-1, 3)
    min_b = all_pts.min(axis=0)
    max_b = all_pts.max(axis=0)
    max_range = (max_b - min_b).max() / 1.75
    mid = (max_b + min_b) / 2.0
    
    for i, (vname, elev, azim) in enumerate(views, 1):
        ax = fig.add_subplot(2, 2, i, projection='3d')
        ax.set_facecolor('#ffffff')
        
        poly = Poly3DCollection(verts, facecolors=face_color, edgecolors=edge_color, linewidth=0.25, alpha=0.92, shade=True)
        ax.add_collection3d(poly)
        
        ax.set_xlim(mid[0] - max_range, mid[0] + max_range)
        ax.set_ylim(mid[1] - max_range, mid[1] + max_range)
        ax.set_zlim(mid[2] - max_range, mid[2] + max_range)
        
        ax.view_init(elev=elev, azim=azim)
        ax.set_title(vname, color='#0f172a', fontsize=12, fontweight='bold', pad=8)
        
        ax.xaxis.pane.fill = False
        ax.yaxis.pane.fill = False
        ax.zaxis.pane.fill = False
        ax.grid(color='#e2e8f0', linestyle=':', alpha=0.8)
        ax.tick_params(colors='#64748b', labelsize=8)
        ax.set_xlabel('X (mm)', color='#64748b', fontsize=8.5)
        ax.set_ylabel('Y (mm)', color='#64748b', fontsize=8.5)
        ax.set_zlabel('Z (mm)', color='#64748b', fontsize=8.5)
        
    fig.suptitle(title, color='#0f172a', fontsize=16, fontweight='bold', y=0.98)
    fig.text(0.5, 0.94, subtitle, ha='center', color='#475569', fontsize=11)
    fig.tight_layout(rect=[0, 0.02, 1, 0.93])
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
    plt.close(fig)
    print(f'Rendered multiview: {out_png}')

def render_exploded_cassette(body_stl: Path, lid_stl: Path, out_png: Path):
    body_verts = load_stl(body_stl)
    lid_verts = load_stl(lid_stl)
    
    # In lid_print.stl, it is printed top-face-down. Flip for assembled view:
    lid_flipped = lid_verts.copy()
    lid_flipped[:, :, 2] = 3.20 - lid_flipped[:, :, 2]
    # Move lid up by 25 mm for exploded view:
    lid_exploded = lid_flipped.copy()
    lid_exploded[:, :, 2] += 32.80 + 22.00
    
    # Glass slide: 25.0 x 75.0 x 1.15 mm at Z = 32.80 + 10.00
    gw, gd, gt = 25.0, 75.0, 1.15
    gz = 32.80 + 10.00
    gx0, gx1 = -gw/2, gw/2
    gy0, gy1 = -gd/2, gd/2
    gz0, gz1 = gz, gz + gt
    glass_box_faces = [
        [[gx0, gy0, gz0], [gx1, gy0, gz0], [gx1, gy1, gz0], [gx0, gy1, gz0]],
        [[gx0, gy0, gz1], [gx0, gy1, gz1], [gx1, gy1, gz1], [gx1, gy0, gz1]],
        [[gx0, gy0, gz0], [gx0, gy1, gz0], [gx0, gy1, gz1], [gx0, gy0, gz1]],
        [[gx1, gy0, gz0], [gx1, gy0, gz1], [gx1, gy1, gz1], [gx1, gy1, gz0]],
        [[gx0, gy0, gz0], [gx1, gy0, gz0], [gx1, gy0, gz1], [gx0, gy0, gz1]],
        [[gx0, gy1, gz0], [gx0, gy1, gz1], [gx1, gy1, gz1], [gx1, gy1, gz0]],
    ]
    
    fig = plt.figure(figsize=(14, 10), dpi=220)
    fig.patch.set_facecolor('#f8fafc')
    ax = fig.add_subplot(1, 1, 1, projection='3d')
    ax.set_facecolor('#ffffff')
    
    # Add body (Sky blue PETG)
    poly_body = Poly3DCollection(body_verts, facecolors='#38bdf8', edgecolors='#0284c7', linewidth=0.2, alpha=0.95, shade=True)
    ax.add_collection3d(poly_body)
    
    # Add glass (Transparent cyan)
    poly_glass = Poly3DCollection(glass_box_faces, facecolors='#67e8f9', edgecolors='#0891b2', linewidth=0.4, alpha=0.45, shade=True)
    ax.add_collection3d(poly_glass)
    
    # Add lid (Slate/Blue PETG)
    poly_lid = Poly3DCollection(lid_exploded, facecolors='#60a5fa', edgecolors='#1d4ed8', linewidth=0.2, alpha=0.92, shade=True)
    ax.add_collection3d(poly_lid)
    
    # Add filament hinge pin (orange line)
    pin_y = np.linspace(-38, 38, 50)
    pin_x = np.full_like(pin_y, -18.2)
    pin_z = np.full_like(pin_y, 32.80 + 22.00 + 0.20)
    ax.plot(pin_x, pin_y, pin_z, color='#f97316', linewidth=2.5)
    
    all_pts = np.vstack([body_verts.reshape(-1, 3), lid_exploded.reshape(-1, 3)])
    min_b, max_b = all_pts.min(axis=0), all_pts.max(axis=0)
    max_range = (max_b - min_b).max() / 1.6
    mid = (max_b + min_b) / 2.0
    
    ax.set_xlim(mid[0] - max_range, mid[0] + max_range)
    ax.set_ylim(mid[1] - max_range, mid[1] + max_range)
    ax.set_zlim(mid[2] - max_range * 0.7, mid[2] + max_range * 0.7)
    
    ax.view_init(elev=24, azim=-55)
    ax.set_title("Small-Parts Cassette v0.8 — Exploded Assembly View", color='#0f172a', fontsize=15, fontweight='bold', pad=12)
    
    ax.text(0, 0, 70, "1. Transverse Hinge Lid (PETG)", color='#1e3a8a', fontsize=11, fontweight='bold')
    ax.text(0, 0, 48, "2. Microscope Glass Slide (75 × 25 × 1.15 mm)", color='#0e7490', fontsize=11, fontweight='bold')
    ax.text(0, 0, 16, "3. Height-Optimized Body (30.8 mm Usable Depth)", color='#0369a1', fontsize=11, fontweight='bold')
    ax.text(-22, 0, 58, "1.75 mm Filament Pin", color='#ea580c', fontsize=10, fontweight='bold')
    
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.grid(color='#e2e8f0', linestyle=':', alpha=0.6)
    ax.tick_params(colors='#64748b', labelsize=8)
    
    fig.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
    plt.close(fig)
    print(f'Rendered exploded cassette: {out_png}')

def render_carrier_stack(carrier_stl: Path, out_png: Path):
    c_verts = load_stl(carrier_stl)
    
    c_upper = c_verts.copy()
    c_upper[:, :, 2] += 49.00
    
    fig = plt.figure(figsize=(15, 9.5), dpi=220)
    fig.patch.set_facecolor('#f8fafc')
    
    ax1 = fig.add_subplot(1, 2, 1, projection='3d')
    ax1.set_facecolor('#ffffff')
    
    poly_low = Poly3DCollection(c_verts, facecolors='#cbd5e1', edgecolors='#64748b', linewidth=0.2, alpha=0.90, shade=True)
    poly_up = Poly3DCollection(c_upper, facecolors='#94a3b8', edgecolors='#475569', linewidth=0.2, alpha=0.90, shade=True)
    ax1.add_collection3d(poly_low)
    ax1.add_collection3d(poly_up)
    
    all_pts = np.vstack([c_verts.reshape(-1, 3), c_upper.reshape(-1, 3)])
    min_b, max_b = all_pts.min(axis=0), all_pts.max(axis=0)
    max_range = (max_b - min_b).max() / 1.7
    mid = (max_b + min_b) / 2.0
    
    ax1.set_xlim(mid[0] - max_range, mid[0] + max_range)
    ax1.set_ylim(mid[1] - max_range, mid[1] + max_range)
    ax1.set_zlim(0, 115)
    
    ax1.view_init(elev=25, azim=-40)
    ax1.set_title("14U Carrier Stack (Isometric 3D)", color='#0f172a', fontsize=12, fontweight='bold')
    ax1.xaxis.pane.fill = False
    ax1.yaxis.pane.fill = False
    ax1.zaxis.pane.fill = False
    ax1.grid(color='#e2e8f0', linestyle=':', alpha=0.6)
    
    ax2 = fig.add_subplot(1, 2, 2)
    ax2.set_facecolor('#ffffff')
    
    ax2.axhline(111.125, color='#dc2626', linestyle='--', linewidth=2, label='Drawer Ceiling (111.125 mm / 4 3/8")')
    ax2.axhline(102.40, color='#2563eb', linestyle='-', linewidth=2, label='14U Stack Top (102.40 mm)')
    ax2.axhline(49.00, color='#059669', linestyle='-', linewidth=1.5, label='Upper Tray Stacking Shelf (49.00 mm)')
    ax2.axhline(44.25, color='#d97706', linestyle=':', linewidth=1.5, label='Upper Foot Protrusion (44.25 mm)')
    ax2.axhline(42.75, color='#7c3aed', linestyle='-.', linewidth=1.5, label='v0.8 Closed Cassette Top (42.75 mm)')
    ax2.axhline(6.75, color='#475569', linestyle='-', linewidth=1.5, label='Cassette Support Floor (6.75 mm)')
    ax2.axhline(0.00, color='#0f172a', linestyle='-', linewidth=2, label='Gridfinity Baseplate (0.00 mm)')
    
    ax2.fill_between([-60, 60], 102.40, 111.125, color='#fee2e2', alpha=0.6, label='Headroom Buffer: 8.725 mm')
    ax2.fill_between([-60, 60], 42.75, 44.25, color='#fef3c7', alpha=0.7, label='Foot Non-Interference: 1.50 mm')
    ax2.fill_between([-55, 55], 6.75, 42.75, color='#ede9fe', alpha=0.5, label='v0.8 Cassette Envelope (36.0 mm)')
    
    ax2.set_xlim(-70, 70)
    ax2.set_ylim(-5, 120)
    ax2.set_title("Vertical Stack & Headroom Tolerance Budget", color='#0f172a', fontsize=12, fontweight='bold')
    ax2.set_ylabel("Height Z (mm)", color='#0f172a', fontsize=10, fontweight='bold')
    ax2.set_xlabel("Width X (mm)", color='#0f172a', fontsize=10, fontweight='bold')
    ax2.legend(loc='upper right', fontsize=8, framealpha=0.95)
    ax2.grid(True, linestyle=':', alpha=0.5)
    
    fig.suptitle("3 × 4 Gridfinity Carrier — 14U Two-Tray Stack Architecture", color='#0f172a', fontsize=15, fontweight='bold', y=0.98)
    fig.tight_layout(rect=[0, 0.02, 1, 0.94])
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
    plt.close(fig)
    print(f'Rendered carrier stack: {out_png}')

def main():
    docs_img = Path('docs/images')
    docs_img.mkdir(parents=True, exist_ok=True)
    
    body_stl = Path('Cassettes/glass_slide_cassette_40x80/build/cassette_body_v0_8.stl')
    lid_stl = Path('Cassettes/glass_slide_cassette_40x80/build/cassette_lid_v0_8_print.stl')
    carrier_stl = Path('Carriers/carrier_3x4_14u_test/build/carrier_3x4_7u_v0_1.stl')
    coupon_stl = Path('Cassettes/divider_fit_coupon_v0_1/build/divider_slot_coupon.stl')
    
    # 1. Exploded Assembly
    render_exploded_cassette(body_stl, lid_stl, docs_img / 'cassette_v0_8_exploded_assembly.png')
    
    # 2. 14U Carrier Stack & Sectional Budget
    render_carrier_stack(carrier_stl, docs_img / 'carrier_3x4_14u_stack.png')
    
    # 3. Multiviews
    render_multiview(body_stl, docs_img / 'cassette_body_v0_8_multiview.png',
                     "Small-Parts Cassette v0.8 Body",
                     "Nominal 38.6 × 80.0 × 32.8 mm · 30.8 mm usable internal depth · 2.0 mm solid floor",
                     face_color='#38bdf8', edge_color='#0284c7')
                     
    render_multiview(lid_stl, docs_img / 'cassette_lid_v0_8_multiview.png',
                     "Small-Parts Cassette v0.8 / v0.7 Lid (Print Top-Face Down)",
                     "27.0 × 1.4 mm end-loaded channel · 6.75 mm compliant PETG latch · 3-knuckle filament hinge",
                     face_color='#60a5fa', edge_color='#1d4ed8')
                     
    render_multiview(carrier_stl, docs_img / 'carrier_3x4_7u_multiview.png',
                     "3 × 4 Gridfinity Carrier Tray (7U Height)",
                     "125.5 × 167.5 × 53.4 mm outside · 120.3 × 162.3 mm throat · accommodates 6 cassettes",
                     face_color='#cbd5e1', edge_color='#475569')
                     
    render_multiview(coupon_stl, docs_img / 'divider_coupon_multiview.png',
                     "Plan 003 — Divider Fit Coupon",
                     "4 slot tolerance stations: 1.30 mm, 1.40 mm, 1.50 mm, 1.60 mm · 0.6 mm floor groove",
                     face_color='#a7f3d0', edge_color='#059669')

if __name__ == '__main__':
    main()
