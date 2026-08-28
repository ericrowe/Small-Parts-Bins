#!/usr/bin/env python3
"""Headless LookAt depth-buffer orthographic multi-view generator for binary STLs."""

from __future__ import annotations

import math
import struct
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def load_stl(path: Path) -> np.ndarray:
    with path.open('rb') as f:
        f.read(80)
        num_triangles = struct.unpack('<I', f.read(4))[0]
        data = f.read()
    
    dt = np.dtype([
        ('normal', np.float32, (3,)),
        ('v0', np.float32, (3,)),
        ('v1', np.float32, (3,)),
        ('v2', np.float32, (3,)),
        ('attr', np.uint16, (1,))
    ])
    arr = np.frombuffer(data, dtype=dt, count=num_triangles)
    verts = np.stack([arr['v0'], arr['v1'], arr['v2']], axis=1)
    return verts

def look_at(eye: np.ndarray, target: np.ndarray, up: np.ndarray) -> np.ndarray:
    forward = target - eye
    forward = forward / np.linalg.norm(forward)
    right = np.cross(forward, up)
    if np.linalg.norm(right) < 1e-6:
        right = np.array([1.0, 0.0, 0.0])
    else:
        right = right / np.linalg.norm(right)
    actual_up = np.cross(right, forward)
    mat = np.eye(4, dtype=np.float32)
    mat[0, :3] = right
    mat[1, :3] = actual_up
    mat[2, :3] = -forward
    mat[:3, 3] = -mat[:3, :3] @ eye
    return mat

def render_mesh(verts: np.ndarray, width: int, height: int, view_mat: np.ndarray,
                scale: float = 1.0, offset: tuple[float, float] = (0.0, 0.0),
                color: tuple[int, int, int] = (56, 189, 248), bg: tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
    v_hom = np.pad(verts, ((0, 0), (0, 0), (0, 1)), constant_values=1.0)
    v_trans = (v_hom @ view_mat.T)[:, :, :3]
    
    screen_x = width / 2.0 + (v_trans[:, :, 0] + offset[0]) * scale
    screen_y = height / 2.0 - (v_trans[:, :, 1] + offset[1]) * scale
    depth_z = v_trans[:, :, 2]
    
    v0 = verts[:, 0, :]
    v1 = verts[:, 1, :]
    v2 = verts[:, 2, :]
    normals = np.cross(v1 - v0, v2 - v0)
    n_len = np.linalg.norm(normals, axis=1, keepdims=True)
    normals = np.divide(normals, n_len, out=np.zeros_like(normals), where=n_len > 1e-6)
    
    view_dir = np.array([0, 0, 1], dtype=np.float32)
    key_light = np.array([-0.577, 0.577, 0.577], dtype=np.float32)
    fill_light = np.array([0.707, 0.707, 0.0], dtype=np.float32)
    
    cam_normals = (normals @ view_mat[:3, :3].T)
    front_facing = (cam_normals @ view_dir) < 0.05
    
    img_rgb = np.full((height, width, 3), bg, dtype=np.uint8)
    zbuffer = np.full((height, width), np.inf, dtype=np.float32)
    
    col = np.array(color, dtype=np.float32)
    tri_indices = np.where(front_facing)[0]
    
    dot1 = np.maximum(0, -np.sum(normals * key_light, axis=1))
    dot2 = np.maximum(0, -np.sum(normals * fill_light, axis=1))
    intensity = np.clip(0.40 + 0.45 * dot1 + 0.15 * dot2, 0.25, 1.0)
    
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
            zbuffer[min_y:max_y+1, min_x:max_x+1][z_mask] = pz[z_mask]
            tri_col = (col * intensity[idx]).astype(np.uint8)
            img_rgb[min_y:max_y+1, min_x:max_x+1][z_mask] = tri_col
            
    return Image.fromarray(img_rgb)

def render_multiview(stl_path: Path, out_path: Path, title: str = "", subtitle: str = ""):
    verts = load_stl(stl_path)
    min_pt = np.min(verts, axis=(0, 1))
    max_pt = np.max(verts, axis=(0, 1))
    center = (min_pt + max_pt) / 2.0
    v_centered = verts - center
    max_dim = np.max(max_pt - min_pt)
    
    w, h = 800, 600
    scale = (w * 0.40) / max_dim
    
    # 4 views: Isometric, Top (XY), Front (XZ), Right (YZ)
    iso_mat = look_at(np.array([1.0, -1.0, 1.0]), np.array([0.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0]))
    top_mat = look_at(np.array([0.0, 0.0, 1.0]), np.array([0.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0]))
    front_mat = look_at(np.array([0.0, -1.0, 0.0]), np.array([0.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0]))
    right_mat = look_at(np.array([1.0, 0.0, 0.0]), np.array([0.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0]))
    
    img_iso = render_mesh(v_centered, w, h, iso_mat, scale=scale)
    img_top = render_mesh(v_centered, w, h, top_mat, scale=scale)
    img_front = render_mesh(v_centered, w, h, front_mat, scale=scale)
    img_right = render_mesh(v_centered, w, h, right_mat, scale=scale)
    
    canvas = Image.new('RGB', (1600, 1200), (255, 255, 255))
    canvas.paste(img_iso, (0, 0))
    canvas.paste(img_top, (800, 0))
    canvas.paste(img_front, (0, 600))
    canvas.paste(img_right, (800, 600))
    
    draw = ImageDraw.Draw(canvas)
    draw.text((40, 40), title or stl_path.name, fill=(15, 23, 42))
    draw.text((40, 65), subtitle or f"Dimensions: {max_pt[0]-min_pt[0]:.1f} × {max_pt[1]-min_pt[1]:.1f} × {max_pt[2]-min_pt[2]:.1f} mm", fill=(100, 116, 139))
    draw.text((40, 100), "Isometric View (3D)", fill=(15, 23, 42))
    draw.text((840, 100), "Top View (XY Plan)", fill=(15, 23, 42))
    draw.text((40, 640), "Front Elevation View (XZ)", fill=(15, 23, 42))
    draw.text((840, 640), "Right Elevation View (YZ)", fill=(15, 23, 42))
    
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)
    print(f"Rendered multi-view sheet: {out_path}")

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <path_to_stl> [output.png]", file=sys.stderr)
        sys.exit(1)
    stl_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else stl_path.with_suffix('.png')
    render_multiview(stl_path, out_path)

if __name__ == "__main__":
    main()
