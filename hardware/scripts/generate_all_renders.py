#!/usr/bin/env python3
"""Generate crisp, high-resolution CAD renders using a pure Z-buffer software rasterizer."""

from __future__ import annotations

import struct, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
from pathlib import Path

# Typography
FONT_PATH = '/System/Library/Fonts/Helvetica.ttc'
try:
    FONT_TITLE = ImageFont.truetype(FONT_PATH, 30, index=0)
    FONT_SUBTITLE = ImageFont.truetype(FONT_PATH, 16, index=0)
    FONT_PANEL = ImageFont.truetype(FONT_PATH, 20, index=0)
    FONT_LABEL = ImageFont.truetype(FONT_PATH, 16, index=0)
except Exception:
    FONT_TITLE = ImageFont.load_default()
    FONT_SUBTITLE = ImageFont.load_default()
    FONT_PANEL = ImageFont.load_default()
    FONT_LABEL = ImageFont.load_default()

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

def sobel_grad(arr: np.ndarray) -> np.ndarray:
    gx = np.zeros_like(arr)
    gy = np.zeros_like(arr)
    gx[1:-1, 1:-1] = ((arr[:-2, 2:] + 2*arr[1:-1, 2:] + arr[2:, 2:]) - 
                      (arr[:-2, :-2] + 2*arr[1:-1, :-2] + arr[2:, :-2])) / 8.0
    gy[1:-1, 1:-1] = ((arr[2:, :-2] + 2*arr[2:, 1:-1] + arr[2:, 2:]) - 
                      (arr[:-2, :-2] + 2*arr[:-2, 1:-1] + arr[:-2, 2:])) / 8.0
    return np.sqrt(gx**2 + gy**2)

def create_lookat_matrix(eye, target, up=np.array([0, 0, 1], dtype=np.float32)):
    eye = np.array(eye, dtype=np.float32)
    target = np.array(target, dtype=np.float32)
    up = np.array(up, dtype=np.float32)
    
    forward = target - eye
    forward = forward / np.linalg.norm(forward)
    
    if abs(np.dot(forward, up)) > 0.999:
        up = np.array([0, 1, 0], dtype=np.float32)
        
    right = np.cross(forward, up)
    right = right / np.linalg.norm(right)
    
    true_up = np.cross(right, forward)
    true_up = true_up / np.linalg.norm(true_up)
    
    return np.vstack([right, true_up, forward])

def render_lookat_scene(
    meshes: list[tuple[np.ndarray, tuple[int,int,int], float]],
    eye,
    target,
    width=1800, height=1200,
    bg_color=(248, 250, 252),
    fit_ratio=0.74
) -> Image.Image:
    R = create_lookat_matrix(eye, target)
    eye = np.array(eye, dtype=np.float32)
    
    transformed_meshes = []
    all_cam_pts = []
    for verts, col, alpha in meshes:
        v_shifted = verts - eye
        cam_verts = np.einsum('ij,ntj->nti', R, v_shifted)
        transformed_meshes.append((cam_verts, np.array(col, dtype=np.uint8), alpha))
        all_cam_pts.append(cam_verts.reshape(-1, 3))
        
    all_cam_pts = np.vstack(all_cam_pts)
    extents_x = np.ptp(all_cam_pts[:, 0])
    extents_y = np.ptp(all_cam_pts[:, 1])
    max_dim = max(extents_x, extents_y)
    scale = (min(width, height) * fit_ratio) / max_dim
    
    center_cam = (all_cam_pts.min(axis=0) + all_cam_pts.max(axis=0)) / 2.0
    
    zbuffer = np.full((height, width), 1e9, dtype=np.float32)
    img_rgb = np.full((height, width, 3), bg_color, dtype=np.uint8)
    normal_map = np.zeros((height, width, 3), dtype=np.float32)
    
    key_light = np.array([0.4, 0.6, -0.7])
    key_light /= np.linalg.norm(key_light)
    fill_light = np.array([-0.5, -0.4, -0.5])
    fill_light /= np.linalg.norm(fill_light)
    
    opaque_meshes = [m for m in transformed_meshes if m[2] >= 0.99]
    translucent_meshes = [m for m in transformed_meshes if m[2] < 0.99]
    
    for cam_verts, col, _ in opaque_meshes:
        screen_x = (cam_verts[:, :, 0] - center_cam[0]) * scale + (width / 2.0)
        screen_y = -(cam_verts[:, :, 1] - center_cam[1]) * scale + (height / 2.0)
        depth_z = cam_verts[:, :, 2]
        
        u = cam_verts[:, 1, :] - cam_verts[:, 0, :]
        v = cam_verts[:, 2, :] - cam_verts[:, 0, :]
        normals = np.cross(u, v)
        norms = np.linalg.norm(normals, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        normals = normals / norms
        
        front_facing = normals[:, 2] < 0
        tri_indices = np.where(front_facing)[0]
        
        dot1 = np.maximum(0, -np.sum(normals * key_light, axis=1))
        dot2 = np.maximum(0, -np.sum(normals * fill_light, axis=1))
        intensity = 0.38 + 0.48 * dot1 + 0.14 * dot2
        intensity = np.clip(intensity, 0.20, 1.0)
        
        for idx in tri_indices:
            x0, x1, x2 = screen_x[idx]
            y0, y1, y2 = screen_y[idx]
            z0, z1, z2 = depth_z[idx]
            norm = normals[idx]
            
            min_x = max(0, int(np.floor(min(x0, x1, x2))))
            max_x = min(width - 1, int(np.ceil(max(x0, x1, x2))))
            min_y = max(0, int(np.floor(min(y0, y1, y2))))
            max_y = min(height - 1, int(np.ceil(max(y0, y1, y2))))
            
            if min_x > max_x or min_y > max_y: continue
            denom = (y1 - y2)*(x0 - x2) + (x2 - x1)*(y0 - y2)
            if abs(denom) < 1e-6: continue
            
            px, py = np.meshgrid(np.arange(min_x, max_x + 1), np.arange(min_y, max_y + 1))
            w0 = ((y1 - y2)*(px - x2) + (x2 - x1)*(py - y2)) / denom
            w1 = ((y2 - y0)*(px - x2) + (x0 - x2)*(py - y2)) / denom
            w2 = 1.0 - w0 - w1
            mask = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
            if not np.any(mask): continue
            
            pz = w0 * z0 + w1 * z1 + w2 * z2
            z_mask = mask & (pz < zbuffer[min_y:max_y+1, min_x:max_x+1])
            if np.any(z_mask):
                tri_col = (col * intensity[idx]).astype(np.uint8)
                cur_zbuf = zbuffer[min_y:max_y+1, min_x:max_x+1]
                cur_img = img_rgb[min_y:max_y+1, min_x:max_x+1]
                cur_norm = normal_map[min_y:max_y+1, min_x:max_x+1]
                
                cur_zbuf[z_mask] = pz[z_mask]
                cur_img[z_mask] = tri_col
                cur_norm[z_mask] = norm
                
                zbuffer[min_y:max_y+1, min_x:max_x+1] = cur_zbuf
                img_rgb[min_y:max_y+1, min_x:max_x+1] = cur_img
                normal_map[min_y:max_y+1, min_x:max_x+1] = cur_norm
                
    z_valid = np.where(zbuffer < 1e8, zbuffer, 0)
    grad_z = sobel_grad(z_valid)
    depth_edge = grad_z > (scale * 0.15)
    
    gn_x = sobel_grad(normal_map[:, :, 0])
    gn_y = sobel_grad(normal_map[:, :, 1])
    gn_z = sobel_grad(normal_map[:, :, 2])
    normal_edge = (gn_x**2 + gn_y**2 + gn_z**2) > 0.12
    
    is_geom = zbuffer < 1e8
    edge_mask = is_geom & (depth_edge | normal_edge)
    img_rgb[edge_mask] = np.array([15, 23, 42], dtype=np.uint8)
    
    for cam_verts, col, alpha in translucent_meshes:
        screen_x = (cam_verts[:, :, 0] - center_cam[0]) * scale + (width / 2.0)
        screen_y = -(cam_verts[:, :, 1] - center_cam[1]) * scale + (height / 2.0)
        depth_z = cam_verts[:, :, 2]
        
        u = cam_verts[:, 1, :] - cam_verts[:, 0, :]
        v = cam_verts[:, 2, :] - cam_verts[:, 0, :]
        normals = np.cross(u, v)
        norms = np.linalg.norm(normals, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        normals = normals / norms
        
        front_facing = normals[:, 2] < 0
        tri_indices = np.where(front_facing)[0]
        
        dot1 = np.maximum(0, -np.sum(normals * key_light, axis=1))
        dot2 = np.maximum(0, -np.sum(normals * fill_light, axis=1))
        intensity = 0.40 + 0.45 * dot1 + 0.15 * dot2
        intensity = np.clip(intensity, 0.25, 1.0)
        
        for idx in tri_indices:
            x0, x1, x2 = screen_x[idx]
            y0, y1, y2 = screen_y[idx]
            z0, z1, z2 = depth_z[idx]
            
            min_x = max(0, int(np.floor(min(x0, x1, x2))))
            max_x = min(width - 1, int(np.ceil(max(x0, x1, x2))))
            min_y = max(0, int(np.floor(min(y0, y1, y2))))
            max_y = min(height - 1, int(np.ceil(max(y0, y1, y2))))
            
            if min_x > max_x or min_y > max_y: continue
            denom = (y1 - y2)*(x0 - x2) + (x2 - x1)*(y0 - y2)
            if abs(denom) < 1e-6: continue
            
            px, py = np.meshgrid(np.arange(min_x, max_x + 1), np.arange(min_y, max_y + 1))
            w0 = ((y1 - y2)*(px - x2) + (x2 - x1)*(py - y2)) / denom
            w1 = ((y2 - y0)*(px - x2) + (x0 - x2)*(py - y2)) / denom
            w2 = 1.0 - w0 - w1
            mask = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
            if not np.any(mask): continue
            
            pz = w0 * z0 + w1 * z1 + w2 * z2
            z_mask = mask & (pz < zbuffer[min_y:max_y+1, min_x:max_x+1])
            if np.any(z_mask):
                tri_col = (col * intensity[idx]).astype(np.float32)
                cur_img = img_rgb[min_y:max_y+1, min_x:max_x+1].astype(np.float32)
                blended = (1.0 - alpha) * cur_img[z_mask] + alpha * tri_col
                img_rgb[min_y:max_y+1, min_x:max_x+1][z_mask] = blended.astype(np.uint8)
                
    return Image.fromarray(img_rgb)

def make_box(x0, x1, y0, y1, z0, z1):
    tris = [
        [[x0, y0, z0], [x1, y1, z0], [x1, y0, z0]], [[x0, y0, z0], [x0, y1, z0], [x1, y1, z0]],
        [[x0, y0, z1], [x1, y0, z1], [x1, y1, z1]], [[x0, y0, z1], [x1, y1, z1], [x0, y1, z1]],
        [[x0, y0, z0], [x0, y1, z1], [x0, y1, z0]], [[x0, y0, z0], [x0, y0, z1], [x0, y1, z1]],
        [[x1, y0, z0], [x1, y1, z0], [x1, y1, z1]], [[x1, y0, z0], [x1, y1, z1], [x1, y0, z1]],
        [[x0, y0, z0], [x1, y0, z0], [x1, y0, z1]], [[x0, y0, z0], [x1, y0, z1], [x0, y0, z1]],
        [[x0, y1, z0], [x1, y1, z1], [x1, y1, z0]], [[x0, y1, z0], [x0, y1, z1], [x1, y1, z1]],
    ]
    return np.array(tris, dtype=np.float32)

def render_exploded_cassette(body_stl: Path, lid_stl: Path, out_png: Path):
    body_verts = load_stl(body_stl)
    lid_verts = load_stl(lid_stl)
    
    # Flip lid right-side up (Z = 3.20 - Z_print) and explode upwards
    lid_flipped = lid_verts.copy()
    lid_flipped[:, :, 2] = 3.20 - lid_flipped[:, :, 2]
    lid_flipped[:, :, 2] += 32.80 + 46.00
    
    gw, gd, gt = 25.0, 75.0, 1.15
    gz = 32.80 + 22.00
    glass_verts = make_box(-gw/2, gw/2, -gd/2, gd/2, gz, gz+gt)
    pin_verts = make_box(-18.2-0.875, -18.2+0.875, -38.0, 38.0, 32.80+46.00-0.875, 32.80+46.00+0.875)
    
    scene = [
        (body_verts, (56, 189, 248), 1.0),
        (glass_verts, (165, 243, 252), 0.55),
        (lid_flipped, (96, 165, 250), 1.0),
        (pin_verts, (249, 115, 22), 1.0),
    ]
    
    rendered_img = render_lookat_scene(scene, eye=(125, -165, 140), target=(0, 0, 40), width=1800, height=1300)
    
    canvas = rendered_img.copy()
    draw = ImageDraw.Draw(canvas)
    
    # Header
    draw.text((50, 40), "Small-Parts Cassette v0.8 — Exploded Assembly View", fill=(15, 23, 42), font=FONT_TITLE)
    draw.text((50, 80), "Individually closed, glass-window modular cassette with removable 1.75 mm filament hinge pin", fill=(71, 85, 105), font=FONT_SUBTITLE)
    
    # Leader line 1: Lid
    draw.line([(1200, 200), (1050, 240)], fill=(30, 58, 138), width=2)
    draw.text((1210, 190), "1. Transverse Hinge Lid (PETG, 3.2 mm)", fill=(30, 58, 138), font=FONT_LABEL)
    draw.text((1210, 215), "   Integral 6.75 mm compliant latch & end-load channel", fill=(71, 85, 105), font=FONT_SUBTITLE)
    
    # Leader line 2: Pin
    draw.line([(320, 240), (560, 310)], fill=(234, 88, 12), width=2)
    draw.text((100, 230), "2. 1.75 mm Filament Hinge Pin", fill=(234, 88, 12), font=FONT_LABEL)
    
    # Leader line 3: Glass
    draw.line([(1200, 420), (1070, 430)], fill=(14, 116, 144), width=2)
    draw.text((1210, 410), "3. Microscope Glass Slide", fill=(14, 116, 144), font=FONT_LABEL)
    draw.text((1210, 435), "   75 × 25 × 1.15 mm replaceable pane", fill=(71, 85, 105), font=FONT_SUBTITLE)
    
    # Leader line 4: Body
    draw.line([(1200, 720), (1100, 680)], fill=(3, 105, 161), width=2)
    draw.text((1210, 710), "4. Height-Optimized Body (PETG/ASA)", fill=(3, 105, 161), font=FONT_LABEL)
    draw.text((1210, 735), "   38.6 × 80.0 × 32.8 mm · 30.8 mm usable depth", fill=(71, 85, 105), font=FONT_SUBTITLE)
    
    canvas.save(out_png)
    print(f"Rendered exploded cassette: {out_png}")

def render_carrier_stack_sheet(carrier_stl: Path, out_png: Path):
    c_verts = load_stl(carrier_stl)
    
    c_upper = c_verts.copy()
    c_upper[:, :, 2] += 49.00
    
    stack_scene = [
        (c_verts, (203, 213, 225), 1.0),
        (c_upper, (148, 163, 184), 1.0)
    ]
    
    # Isometric 3D Stack looking into cavity from front-right-top
    img_stack = render_lookat_scene(stack_scene, eye=(190, -220, 200), target=(0, 0, 50), width=900, height=950, fit_ratio=0.78)
    
    # Matplotlib 2D Vertical Datum Diagram
    fig = plt.figure(figsize=(7.5, 8.0), dpi=120)
    fig.patch.set_facecolor('#ffffff')
    ax = fig.add_subplot(1, 1, 1)
    ax.set_facecolor('#ffffff')
    
    ax.axhline(111.125, color='#dc2626', linestyle='--', linewidth=2.5, label='Drawer Ceiling (111.125 mm / 4 3/8")')
    ax.axhline(102.40, color='#2563eb', linestyle='-', linewidth=2.0, label='14U Stack Top (102.40 mm)')
    ax.axhline(49.00, color='#059669', linestyle='-', linewidth=1.8, label='Upper Tray Stacking Shelf (49.00 mm)')
    ax.axhline(44.25, color='#d97706', linestyle=':', linewidth=2.0, label='Upper Foot Protrusion (44.25 mm)')
    ax.axhline(42.75, color='#7c3aed', linestyle='-.', linewidth=1.8, label='v0.8 Closed Cassette Top (42.75 mm)')
    ax.axhline(6.75, color='#475569', linestyle='-', linewidth=1.8, label='Cassette Support Floor (6.75 mm)')
    ax.axhline(0.00, color='#0f172a', linestyle='-', linewidth=2.2, label='Gridfinity Baseplate (0.00 mm)')
    
    ax.fill_between([-60, 60], 102.40, 111.125, color='#fee2e2', alpha=0.7, label='Headroom Buffer: 8.725 mm')
    ax.fill_between([-60, 60], 42.75, 44.25, color='#fef3c7', alpha=0.8, label='Foot Non-Interference: 1.50 mm')
    ax.fill_between([-55, 55], 6.75, 42.75, color='#ede9fe', alpha=0.55, label='v0.8 Cassette Envelope (36.0 mm)')
    
    ax.set_xlim(-65, 65)
    ax.set_ylim(-4, 118)
    ax.set_title("Vertical Stack & Clearance Budget", color='#0f172a', fontsize=13, fontweight='bold', pad=10)
    ax.set_ylabel("Height Z (mm)", color='#0f172a', fontsize=11, fontweight='bold')
    ax.set_xlabel("Width X (mm)", color='#0f172a', fontsize=11, fontweight='bold')
    ax.legend(loc='upper right', fontsize=9, framealpha=0.95)
    ax.grid(True, linestyle=':', alpha=0.6)
    fig.tight_layout()
    
    diagram_path = out_png.parent / 'temp_diagram.png'
    fig.savefig(diagram_path, facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close(fig)
    img_diagram = Image.open(diagram_path)
    
    canvas = Image.new('RGB', (1800, 1200), color=(248, 250, 252))
    draw = ImageDraw.Draw(canvas)
    draw.text((50, 35), "3 × 4 Gridfinity Carrier — 14U Stack Architecture", fill=(15, 23, 42), font=FONT_TITLE)
    draw.text((50, 75), "Physically verified 2-tray vertical stack (Plan 001) with 8.725 mm drawer headroom clearance", fill=(71, 85, 105), font=FONT_SUBTITLE)
    
    canvas.paste(img_stack, (40, 120))
    diag_resized = img_diagram.resize((820, 950), Image.Resampling.LANCZOS)
    canvas.paste(diag_resized, (920, 120))
    
    canvas.save(out_png)
    diagram_path.unlink(missing_ok=True)
    print(f"Rendered carrier stack: {out_png}")

def make_multiview_sheet(verts: np.ndarray, title: str, subtitle: str, out_png: Path, color=(56, 189, 248)):
    target = np.mean(verts.reshape(-1, 3), axis=0)
    
    img_iso = render_lookat_scene([(verts, color, 1.0)], eye=target + np.array([110, -150, 120]), target=target, width=820, height=560, fit_ratio=0.74)
    img_top = render_lookat_scene([(verts, color, 1.0)], eye=target + np.array([0, 0, 300]), target=target, width=820, height=560, fit_ratio=0.74)
    img_front = render_lookat_scene([(verts, color, 1.0)], eye=target + np.array([0, -300, 0]), target=target, width=820, height=560, fit_ratio=0.74)
    img_side = render_lookat_scene([(verts, color, 1.0)], eye=target + np.array([300, 0, 0]), target=target, width=820, height=560, fit_ratio=0.74)
    
    canvas = Image.new('RGB', (1800, 1350), color=(248, 250, 252))
    draw = ImageDraw.Draw(canvas)
    
    draw.text((50, 30), title, fill=(15, 23, 42), font=FONT_TITLE)
    draw.text((50, 70), subtitle, fill=(71, 85, 105), font=FONT_SUBTITLE)
    
    canvas.paste(img_iso, (50, 110))
    draw.text((70, 125), "Isometric View (3D)", fill=(15, 23, 42), font=FONT_PANEL)
    
    canvas.paste(img_top, (930, 110))
    draw.text((950, 125), "Top View (XY Plan)", fill=(15, 23, 42), font=FONT_PANEL)
    
    canvas.paste(img_front, (50, 720))
    draw.text((70, 735), "Front Elevation View (XZ)", fill=(15, 23, 42), font=FONT_PANEL)
    
    canvas.paste(img_side, (930, 720))
    draw.text((950, 735), "Right Elevation View (YZ)", fill=(15, 23, 42), font=FONT_PANEL)
    
    canvas.save(out_png)
    print(f"Rendered multiview: {out_png}")

def main():
    docs_img = Path('docs/images')
    docs_img.mkdir(parents=True, exist_ok=True)
    
    body_stl = Path('hardware/cassettes/glass_slide_cassette_40x80/build/cassette_body_v0_8.stl')
    lid_stl = Path('hardware/cassettes/glass_slide_cassette_40x80/build/cassette_lid_v0_8_print.stl')
    carrier_stl = Path('hardware/carriers/carrier_3x4_14u_test/build/carrier_3x4_7u_v0_1.stl')
    
    # 1. Exploded Assembly
    render_exploded_cassette(body_stl, lid_stl, docs_img / 'cassette_v0_8_exploded_assembly.png')
    
    # 2. 14U Carrier Stack & Sectional Budget
    render_carrier_stack_sheet(carrier_stl, docs_img / 'carrier_3x4_14u_stack.png')
    
    # 3. Multiviews
    body_verts = load_stl(body_stl)
    make_multiview_sheet(body_verts, "Small-Parts Cassette v0.8 Body",
                         "Nominal 38.6 × 80.0 × 32.8 mm · 30.8 mm usable internal depth · 2.0 mm solid floor",
                         docs_img / 'cassette_body_v0_8_multiview.png', color=(56, 189, 248))
                         
    lid_verts = load_stl(lid_stl)
    lid_flipped = lid_verts.copy()
    lid_flipped[:, :, 2] = 3.20 - lid_flipped[:, :, 2]
    make_multiview_sheet(lid_flipped, "Small-Parts Cassette v0.8 / v0.7 Transverse Lid",
                         "27.0 × 1.4 mm end-loaded channel · 6.75 mm compliant PETG latch · 3-knuckle filament hinge",
                         docs_img / 'cassette_lid_v0_8_multiview.png', color=(96, 165, 250))
                         
    carrier_verts = load_stl(carrier_stl)
    make_multiview_sheet(carrier_verts, "3 × 4 Gridfinity Carrier Tray (7U Height)",
                         "125.5 × 167.5 × 53.4 mm outside · 120.3 × 162.3 mm throat · accommodates 6 cassettes",
                         docs_img / 'carrier_3x4_7u_multiview.png', color=(148, 163, 184))

    # Copy to component build folders
    shutil.copy('docs/images/cassette_v0_8_exploded_assembly.png', 'hardware/cassettes/glass_slide_cassette_40x80/build/cassette_v0_8_exploded_assembly.png')
    shutil.copy('docs/images/cassette_body_v0_8_multiview.png', 'hardware/cassettes/glass_slide_cassette_40x80/build/cassette_body_v0_8_multiview.png')
    shutil.copy('docs/images/cassette_lid_v0_8_multiview.png', 'hardware/cassettes/glass_slide_cassette_40x80/build/cassette_lid_v0_8_multiview.png')
    shutil.copy('docs/images/carrier_3x4_14u_stack.png', 'hardware/carriers/carrier_3x4_14u_test/build/carrier_3x4_14u_stack.png')
    shutil.copy('docs/images/carrier_3x4_7u_multiview.png', 'hardware/carriers/carrier_3x4_14u_test/build/carrier_3x4_7u_multiview.png')
    print('All CAD renders regenerated successfully.')

if __name__ == '__main__':
    main()
