---
name: cad-renderer
description: >-
  Generate headless 3D multi-view engineering sheets and exploded assembly drawings
  from binary STL files using a software depth-buffer renderer. Use this skill when
  creating documentation renders, updating README 3D galleries, or visually inspecting models.
---

# CAD Renderer Skill

This skill renders crisp 2D orthographic engineering multi-view sheets (Top, Front, Right, Isometric) and exploded assembly diagrams directly from binary STL files without requiring a GPU or CAD software installed.

## How to Render an STL

Run the script from the command line:

```bash
python3 .agents/skills/cad-renderer/scripts/render_multiview.py path/to/model.stl [output_image.png]
```

## Features
- **LookAt Matrix & Z-Buffer Engine:** Accurate occlusion and depth sorting.
- **2-Point Directional Lighting:** High-contrast key and fill lighting with ambient occlusion emulation.
- **Vector Outlining:** Crisp engineering drawing aesthetic.
- **Fast Execution:** Standard parts render in under 1 second.
