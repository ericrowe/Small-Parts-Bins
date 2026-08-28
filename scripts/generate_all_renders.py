#!/usr/bin/env python3
"""Generate high-resolution 100% opaque 3D CAD renders of all components with sharp feature lines."""

from __future__ import annotations

import struct, shutil
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection
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

def shade_triangles(verts: np.ndarray, base_color: str, light_dir=(0.45, -0.55, 0.70), fill_dir=(-0.50, 0.50, 0.40)) -> np.ndarray:
    """Calculate key and fill directional lighting for clean solid CAD appearance."""
    base_rgb = np.array(mcolors.to_rgb(base_color))
    
    u = verts[:, 1, :] - verts[:, 0, :]
    v = verts[:, 2, :] - verts[:, 0, :]
    normals = np.cross(u, v)
    norms = np.linalg.norm(normals, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    normals = normals / norms
    
    l1 = np.array(light_dir) / np.linalg.norm(light_dir)
    l2 = np.array(fill_dir) / np.linalg.norm(fill_dir)
    
    dot1 = np.maximum(0, np.sum(normals * l1, axis=1))
    dot2 = np.maximum(0, np.sum(normals * l2, axis=1))
    
    intensity = 0.35 + 0.50 * dot1 + 0.15 * dot2
    intensity = np.clip(intensity, 0.20, 1.0)
    
    return intensity[:, np.newaxis] * base_rgb

def extract_feature_edges(verts: np.ndarray, angle_threshold_deg: float = 25.0) -> np.ndarray:
    """Extract geometric crease lines (dihedral angle > threshold) to avoid mesh triangulation diagonals."""
    cos_thresh = np.cos(np.radians(angle_threshold_deg))
    
    u = verts[:, 1, :] - verts[:, 0, :]
    v = verts[:, 2, :] - verts[:, 0, :]
    normals = np.cross(u, v)
    norms = np.linalg.norm(normals, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    normals = normals / norms
    
    edge_dict = {}
    for tri_idx, (tri, norm) in enumerate(zip(verts, normals)):
        for i in range(3):
            p1 = tuple(np.round(tri[i], 3))
            p2 = tuple(np.round(tri[(i+1)%3], 3))
            edge_key = tuple(sorted((p1, p2)))
            if edge_key not in edge_dict:
                edge_dict[edge_key] = []
            edge_dict[edge_key].append((p1, p2, norm))
            
    feature_lines = []
    for edge_key, face_list in edge_dict.items():
        if len(face_list) == 1:
            p1, p2, _ = face_list[0]
            feature_lines.append([p1, p2])
        elif len(face_list) >= 2:
            n1 = face_list[0][2]
            n2 = face_list[1][2]
            dot = np.dot(n1, n2)
            if dot < cos_thresh:
                p1, p2, _ = face_list[0]
                feature_lines.append([p1, p2])
                
    return np.array(feature_lines) if feature_lines else np.empty((0, 2, 3))

def render_multiview(stl_path: Path, out_png: Path, title: str, subtitle: str, face_color='#38bdf8', line_color='#0284c7'):
    verts = load_stl(stl_path)
    edges = extract_feature_edges(verts, angle_threshold_deg=25.0)
    shaded_colors = shade_triangles(verts, face_color)
    
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
        
        # 100% Solid Opacity with custom directional shading and NO triangulation diagonals
        poly = Poly3DCollection(verts, facecolors=shaded_colors, edgecolors='none', alpha=1.0, shade=False)
        ax.add_collection3d(poly)
        
        # Draw clean sharp geometric crease edges
        if len(edges) > 0:
            lines = Line3DCollection(edges, colors=line_color, linewidths=0.75, alpha=0.9)
            ax.add_collection3d(lines)
        
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
    print(f'Rendered 100% opaque multiview: {out_png}')

def render_exploded_cassette(body_stl: Path, lid_stl: Path, out_png: Path):
    body_verts = load_stl(body_stl)
    lid_verts = load_stl(lid_stl)
    
    body_edges = extract_feature_edges(body_verts, angle_threshold_deg=25.0)
    body_shaded = shade_triangles(body_verts, '#38bdf8')
    
    # Flip lid for assembled right-side-up orientation:
    lid_flipped = lid_verts.copy()
    lid_flipped[:, :, 2] = 3.20 - lid_flipped[:, :, 2]
    
    # Move lid up by 26 mm for exploded view:
    lid_exploded = lid_flipped.copy()
    lid_exploded[:, :, 2] += 32.80 + 26.00
    lid_edges = extract_feature_edges(lid_exploded, angle_threshold_deg=25.0)
    lid_shaded = shade_triangles(lid_exploded, '#60a5fa')
    
    # Glass slide: 25.0 x 75.0 x 1.15 mm at Z = 32.80 + 12.00 (translucent cyan)
    gw, gd, gt = 25.0, 75.0, 1.15
    gz = 32.80 + 12.00
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
    glass_edges = [
        [[gx0, gy0, gz0], [gx1, gy0, gz0]], [[gx1, gy0, gz0], [gx1, gy1, gz0]],
        [[gx1, gy1, gz0], [gx0, gy1, gz0]], [[gx0, gy1, gz0], [gx0, gy0, gz0]],
        [[gx0, gy0, gz1], [gx1, gy0, gz1]], [[gx1, gy0, gz1], [gx1, gy1, gz1]],
        [[gx1, gy1, gz1], [gx0, gy1, gz1]], [[gx0, gy1, gz1], [gx0, gy0, gz1]],
        [[gx0, gy0, gz0], [gx0, gy0, gz1]], [[gx1, gy0, gz0], [gx1, gy0, gz1]],
        [[gx1, gy1, gz0], [gx1, gy1, gz1]], [[gx0, gy1, gz0], [gx0, gy1, gz1]],
    ]
    
    fig = plt.figure(figsize=(14, 10), dpi=220)
    fig.patch.set_facecolor('#f8fafc')
    ax = fig.add_subplot(1, 1, 1, projection='3d')
    ax.set_facecolor('#ffffff')
    
    # 1. 100% Solid Body (Sky blue PETG)
    poly_body = Poly3DCollection(body_verts, facecolors=body_shaded, edgecolors='none', alpha=1.0, shade=False)
    ax.add_collection3d(poly_body)
    if len(body_edges) > 0:
        lines_body = Line3DCollection(body_edges, colors='#0369a1', linewidths=0.75, alpha=0.95)
        ax.add_collection3d(lines_body)
    
    # 2. Translucent Glass Slide (Cyan glass with crisp border lines)
    poly_glass = Poly3DCollection(glass_box_faces, facecolors='#a5f3fc', edgecolors='none', alpha=0.45, shade=False)
    ax.add_collection3d(poly_glass)
    lines_glass = Line3DCollection(glass_edges, colors='#0891b2', linewidths=1.0, alpha=0.9)
    ax.add_collection3d(lines_glass)
    
    # 3. 100% Solid Lid (Royal Blue PETG)
    poly_lid = Poly3DCollection(lid_exploded, facecolors=lid_shaded, edgecolors='none', alpha=1.0, shade=False)
    ax.add_collection3d(poly_lid)
    if len(lid_edges) > 0:
        lines_lid = Line3DCollection(lid_edges, colors='#1d4ed8', linewidths=0.75, alpha=0.95)
        ax.add_collection3d(lines_lid)
    
    # 4. 1.75 mm Filament Pin (Solid Orange line)
    pin_y = np.linspace(-38, 38, 50)
    pin_x = np.full_like(pin_y, -18.2)
    pin_z = np.full_like(pin_y, 32.80 + 26.00 + 0.20)
    ax.plot(pin_x, pin_y, pin_z, color='#ea580c', linewidth=3.0)
    
    all_pts = np.vstack([body_verts.reshape(-1, 3), lid_exploded.reshape(-1, 3)])
    min_b, max_b = all_pts.min(axis=0), all_pts.max(axis=0)
    max_range = (max_b - min_b).max() / 1.6
    mid = (max_b + min_b) / 2.0
    
    ax.set_xlim(mid[0] - max_range, mid[0] + max_range)
    ax.set_ylim(mid[1] - max_range, mid[1] + max_range)
    ax.set_zlim(mid[2] - max_range * 0.7, mid[2] + max_range * 0.7)
    
    ax.view_init(elev=24, azim=-55)
    ax.set_title("Small-Parts Cassette v0.8 — 100% Opaque CAD Exploded View", color='#0f172a', fontsize=15, fontweight='bold', pad=12)
    
    ax.text(0, 0, 74, "1. Transverse Hinge Lid (100% Opaque PETG)", color='#1e3a8a', fontsize=11, fontweight='bold')
    ax.text(0, 0, 50, "2. Microscope Glass Slide (Translucent 1.15 mm Glass)", color='#0e7490', fontsize=11, fontweight='bold')
    ax.text(0, 0, 16, "3. Height-Optimized Body (100% Opaque PETG/ASA)", color='#0369a1', fontsize=11, fontweight='bold')
    ax.text(-22, 0, 62, "1.75 mm Filament Pin", color='#ea580c', fontsize=10, fontweight='bold')
    
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.grid(color='#e2e8f0', linestyle=':', alpha=0.6)
    ax.tick_params(colors='#64748b', labelsize=8)
    
    fig.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
    plt.close(fig)
    print(f'Rendered 100% opaque exploded cassette: {out_png}')

def render_carrier_stack(carrier_stl: Path, out_png: Path):
    c_verts = load_stl(carrier_stl)
    c_edges = extract_feature_edges(c_verts, angle_threshold_deg=25.0)
    c_shaded_low = shade_triangles(c_verts, '#cbd5e1')
    
    c_upper = c_verts.copy()
    c_upper[:, :, 2] += 49.00
    c_shaded_up = shade_triangles(c_upper, '#94a3b8')
    c_upper_edges = c_edges.copy()
    if len(c_upper_edges) > 0:
        c_upper_edges[:, :, 2] += 49.00
    
    fig = plt.figure(figsize=(15, 9.5), dpi=220)
    fig.patch.set_facecolor('#f8fafc')
    
    ax1 = fig.add_subplot(1, 2, 1, projection='3d')
    ax1.set_facecolor('#ffffff')
    
    # 100% Solid Carriers
    poly_low = Poly3DCollection(c_verts, facecolors=c_shaded_low, edgecolors='none', alpha=1.0, shade=False)
    poly_up = Poly3DCollection(c_upper, facecolors=c_shaded_up, edgecolors='none', alpha=1.0, shade=False)
    ax1.add_collection3d(poly_low)
    ax1.add_collection3d(poly_up)
    
    if len(c_edges) > 0:
        ax1.add_collection3d(Line3DCollection(c_edges, colors='#475569', linewidths=0.6, alpha=0.9))
    if len(c_upper_edges) > 0:
        ax1.add_collection3d(Line3DCollection(c_upper_edges, colors='#334155', linewidths=0.6, alpha=0.9))
    
    all_pts = np.vstack([c_verts.reshape(-1, 3), c_upper.reshape(-1, 3)])
    min_b, max_b = all_pts.min(axis=0), all_pts.max(axis=0)
    max_range = (max_b - min_b).max() / 1.7
    mid = (max_b + min_b) / 2.0
    
    ax1.set_xlim(mid[0] - max_range, mid[0] + max_range)
    ax1.set_ylim(mid[1] - max_range, mid[1] + max_range)
    ax1.set_zlim(0, 115)
    
    ax1.view_init(elev=25, azim=-40)
    ax1.set_title("14U Carrier Stack (Solid 100% Opaque 3D)", color='#0f172a', fontsize=12, fontweight='bold')
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
    print(f'Rendered 100% opaque carrier stack: {out_png}')

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
                     face_color='#38bdf8', line_color='#0284c7')
                     
    render_multiview(lid_stl, docs_img / 'cassette_lid_v0_8_multiview.png',
                     "Small-Parts Cassette v0.8 / v0.7 Lid (Print Top-Face Down)",
                     "27.0 × 1.4 mm end-loaded channel · 6.75 mm compliant PETG latch · 3-knuckle filament hinge",
                     face_color='#60a5fa', line_color='#1d4ed8')
                     
    render_multiview(carrier_stl, docs_img / 'carrier_3x4_7u_multiview.png',
                     "3 × 4 Gridfinity Carrier Tray (7U Height)",
                     "125.5 × 167.5 × 53.4 mm outside · 120.3 × 162.3 mm throat · accommodates 6 cassettes",
                     face_color='#cbd5e1', line_color='#475569')
                     
    render_multiview(coupon_stl, docs_img / 'divider_coupon_multiview.png',
                     "Plan 003 — Divider Fit Coupon",
                     "4 slot tolerance stations: 1.30 mm, 1.40 mm, 1.50 mm, 1.60 mm · 0.6 mm floor groove",
                     face_color='#6ee7b7', line_color='#059669')

    # Copy to component build folders
    shutil.copy('docs/images/cassette_v0_8_exploded_assembly.png', 'Cassettes/glass_slide_cassette_40x80/build/cassette_v0_8_exploded_assembly.png')
    shutil.copy('docs/images/cassette_body_v0_8_multiview.png', 'Cassettes/glass_slide_cassette_40x80/build/cassette_body_v0_8_multiview.png')
    shutil.copy('docs/images/cassette_lid_v0_8_multiview.png', 'Cassettes/glass_slide_cassette_40x80/build/cassette_lid_v0_8_multiview.png')
    shutil.copy('docs/images/carrier_3x4_14u_stack.png', 'Carriers/carrier_3x4_14u_test/build/carrier_3x4_14u_stack.png')
    shutil.copy('docs/images/carrier_3x4_7u_multiview.png', 'Carriers/carrier_3x4_14u_test/build/carrier_3x4_7u_multiview.png')
    shutil.copy('docs/images/divider_coupon_multiview.png', 'Cassettes/divider_fit_coupon_v0_1/build/divider_coupon_multiview.png')
    print('All 100% opaque CAD renders generated and copied.')

if __name__ == '__main__':
    main()
