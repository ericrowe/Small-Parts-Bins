"""Hybrid Computer Vision & Fastener Cartridge Ingestor Service.

Processes cartridge hardware photos (or form inputs) to:
1. Detect and OCR rectangular label cutouts (e.g. 'M4 × 6 / Pitch 0.7' with category color header).
2. Calibrate millimeter scale from an optional ruler in frame (or interactive 2-point click).
3. Segment individual fasteners on wood/tray backgrounds and separate them by finish/color
   (Black Oxide vs Silver/Stainless vs Brass) within a single sequential bin.
4. Classify bolt head types (Socket Head Cap SHCS vs Button Head BHCS vs Flat FHCS vs Hex/Pan).
5. Look up canonical engineering drill/tool specs from hardware/labels/data/fasteners.json.
6. Generate interactive clarification questions when no label is present or confidence is low.
7. Render an annotated preview overlay image highlighting the label and numbered part badges.
"""

from __future__ import annotations

import base64
import json
import logging
import math
import os
import re
import shutil
import subprocess
import tempfile
from typing import Any, Dict, List, Optional, Tuple

import cv2
import httpx
import numpy as np

# Prevent OpenCV pthreads/OpenMP thread-pool deadlocks under async FastAPI / Python 3.14
cv2.setNumThreads(1)

from server.app.seed import find_fasteners_json

logger = logging.getLogger(__name__)


def _load_fastener_reference_table() -> Dict[str, Any]:
    """Load thread pitches, tap drills, clearance drills, and hex key sizes from fasteners.json."""
    path = find_fasteners_json()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load fasteners.json: {e}")
    return {"threads": {"metric": [], "imperial": []}, "categories": {}}


def lookup_fastener_specs(size: str, head: str = "shcs", drive: str = "hex") -> Dict[str, str]:
    """Look up pitch, tap_drill, clearance_drill, and tool_key for a given thread size and head style."""
    ref = _load_fastener_reference_table()
    clean_sz = (size or "").strip().upper()
    head_key = (head or "shcs").strip().lower()
    if head_key in ("socket", "cap"):
        head_key = "shcs"
    elif head_key in ("button", "dome"):
        head_key = "bhcs"
    elif head_key in ("flat", "countersunk"):
        head_key = "fhcs"

    for m in ref.get("threads", {}).get("metric", []):
        if m.get("size", "").upper() == clean_sz:
            pitch = m.get("pitch_coarse", "")
            hex_map = m.get("hex_key", {})
            torx_map = m.get("torx_key", {})
            if drive == "torx" and isinstance(torx_map, dict):
                tool_key = torx_map.get(head_key) or torx_map.get("shcs", "")
            elif isinstance(hex_map, dict):
                tool_key = hex_map.get(head_key) or hex_map.get("shcs", "")
            else:
                tool_key = str(hex_map)
            return {
                "pitch": f"{pitch} mm" if pitch and "mm" not in str(pitch) else str(pitch),
                "tap_drill": m.get("tap_drill", ""),
                "clearance_drill": m.get("clearance_drill", ""),
                "tool_key": tool_key,
                "category_id": "metric_coarse",
            }

    for imp in ref.get("threads", {}).get("imperial", []):
        if imp.get("size", "").upper() == clean_sz:
            tpi = imp.get("tpi_coarse", "")
            hex_map = imp.get("hex_key", {})
            tool_key = hex_map.get(head_key, hex_map.get("shcs", "")) if isinstance(hex_map, dict) else str(hex_map)
            return {
                "pitch": f"{tpi} TPI" if tpi and "TPI" not in str(tpi) else str(tpi),
                "tap_drill": imp.get("tap_drill", ""),
                "clearance_drill": imp.get("clearance_drill", ""),
                "tool_key": tool_key,
                "category_id": "imperial_unc",
            }

    return {
        "pitch": "",
        "tap_drill": "",
        "clearance_drill": "",
        "tool_key": "",
        "category_id": "metric_coarse" if clean_sz.startswith("M") else "imperial_unc",
    }


def _run_tesseract_ocr_on_crop(crop_bgr: np.ndarray) -> str:
    """Run tesseract CLI across 4 rotations of a label cutout crop and return combined text."""
    tesseract_bin = shutil.which("tesseract")
    if not tesseract_bin:
        for candidate in ("/opt/homebrew/bin/tesseract", "/usr/local/bin/tesseract", "/usr/bin/tesseract"):
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                tesseract_bin = candidate
                break
    if not tesseract_bin:
        return _opencv_builtin_label_ocr(crop_bgr)

    # Upscale small crops for cleaner OCR
    orig_crop = crop_bgr.copy()
    h, w = crop_bgr.shape[:2]
    scale = max(1.0, 320.0 / max(1, min(h, w)))
    if scale > 1.1:
        crop_bgr = cv2.resize(crop_bgr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
    # Enhance contrast of dark text on white paper
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    collected_texts: List[str] = []
    rotations = [
        binary,
        cv2.rotate(binary, cv2.ROTATE_90_CLOCKWISE),
        cv2.rotate(binary, cv2.ROTATE_90_COUNTERCLOCKWISE),
        cv2.rotate(binary, cv2.ROTATE_180),
    ]

    for rot_img in rotations:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            cv2.imwrite(tmp_path, rot_img)
            for psm in ("6", "11"):
                proc = subprocess.run(
                    [tesseract_bin, tmp_path, "stdout", "--psm", psm],
                    capture_output=True,
                    text=True,
                    timeout=4,
                    check=False,
                )
                if proc.returncode == 0 and proc.stdout.strip():
                    txt = proc.stdout.strip()
                    collected_texts.append(txt)
                    # Early exit if we already clearly matched M<number> x <number>
                    if re.search(r"M\d+(?:\.\d+)?\s*[xX×*]\s*\d+", txt):
                        return "\n".join(collected_texts)
        except Exception as e:
            logger.debug(f"Tesseract rotation pass error: {e}")
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    combined = "\n".join(collected_texts)
    if not re.search(r"M\d+(?:\.\d+)?\s*[xX×*]\s*\d+", combined):
        fallback_txt = _opencv_builtin_label_ocr(orig_crop)
        if fallback_txt:
            combined = f"{combined}\n{fallback_txt}".strip()
    return combined


def _orient_label_crop_upright(crop_bgr: np.ndarray) -> np.ndarray:
    """
    Rotate a label cutout crop so its colored category header bar (blue or orange)
    sits at the TOP edge, making the text horizontal and right-side-up.
    """
    hsv = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2HSV)
    blue_mask = cv2.inRange(hsv, np.array([95, 100, 80]), np.array([135, 255, 255]))
    orange_mask = cv2.inRange(hsv, np.array([5, 110, 100]), np.array([25, 255, 255]))
    color_mask = cv2.bitwise_or(blue_mask, orange_mask)

    ch, cw = color_mask.shape[:2]
    if np.count_nonzero(color_mask) < 20:
        return crop_bgr

    band_h = max(1, int(ch * 0.35))
    band_w = max(1, int(cw * 0.35))
    scores = {
        "top": float(np.mean(color_mask[:band_h, :])),
        "bottom": float(np.mean(color_mask[ch - band_h :, :])),
        "left": float(np.mean(color_mask[:, :band_w])),
        "right": float(np.mean(color_mask[:, cw - band_w :])),
    }
    best_side = max(scores, key=scores.get)
    if best_side == "left":
        return cv2.rotate(crop_bgr, cv2.ROTATE_90_CLOCKWISE)
    if best_side == "right":
        return cv2.rotate(crop_bgr, cv2.ROTATE_90_COUNTERCLOCKWISE)
    if best_side == "bottom":
        return cv2.rotate(crop_bgr, cv2.ROTATE_180)
    return crop_bgr


def _opencv_builtin_label_ocr(crop_bgr: np.ndarray) -> str:
    """
    Pure-Python / OpenCV character glyph recognizer for standardized fastener labels
    (e.g. 'M4 x 6 / Pitch 0.7'). Used when system tesseract binary is not installed on host.
    """
    upright = _orient_label_crop_upright(crop_bgr)
    h, w = upright.shape[:2]
    scale = 240.0 / max(1.0, float(min(h, w)))
    work = cv2.resize(upright, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)
    wh, ww = work.shape[:2]

    hsv = cv2.cvtColor(work, cv2.COLOR_BGR2HSV)
    s_ch = hsv[:, :, 1]
    v_ch = hsv[:, :, 2]

    # Isolate the white paper interior (high V, low S) below the colored header bar
    white_paper = (v_ch >= 145) & (s_ch <= 65)
    white_u8 = np.where(white_paper, 255, 0).astype(np.uint8)
    cnts, _ = cv2.findContours(white_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if cnts:
        main_cnt = max(cnts, key=cv2.contourArea)
        wx, wy, w_w, w_h = cv2.boundingRect(main_cnt)
        if w_w * w_h >= (wh * ww) * 0.15:
            work = work[wy : wy + w_h, wx : wx + w_w]
            wh, ww = work.shape[:2]

    gray = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)
    mx, my = max(2, int(ww * 0.06)), max(2, int(wh * 0.06))
    roi_gray = gray[my : wh - my, mx : ww - mx]
    if roi_gray.size == 0:
        return ""

    med_bg = float(np.percentile(roi_gray, 75))
    ink = np.where(roi_gray < med_bg - 32, 255, 0).astype(np.uint8)
    rh, rw = ink.shape[:2]

    row_sums = np.sum(ink > 0, axis=1)
    active_rows = row_sums >= max(2, int(rw * 0.03))
    lines: List[Tuple[int, int]] = []
    in_line = False
    start_r = 0
    for r_idx, val in enumerate(active_rows):
        if val and not in_line:
            in_line = True
            start_r = r_idx
        elif not val and in_line:
            in_line = False
            if r_idx - start_r >= 8:
                lines.append((start_r, r_idx))
    if in_line and rh - start_r >= 8:
        lines.append((start_r, rh))

    if not lines:
        return ""

    glyph_W, glyph_H = 24, 32
    templates: Dict[str, List[np.ndarray]] = {}
    chars_to_render = ["M", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "x"]
    for ch_str in chars_to_render:
        templates[ch_str] = []
        for font in (cv2.FONT_HERSHEY_SIMPLEX, cv2.FONT_HERSHEY_DUPLEX, cv2.FONT_HERSHEY_TRIPLEX):
            for thick in (2, 3, 4):
                canvas = np.zeros((80, 80), dtype=np.uint8)
                cv2.putText(canvas, ch_str, (10, 60), font, 1.6, 255, thick, cv2.LINE_AA)
                _, c_bin = cv2.threshold(canvas, 100, 255, cv2.THRESH_BINARY)
                ys, xs = np.where(c_bin > 0)
                if ys.size > 0:
                    crop_g = c_bin[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]
                    norm_g = cv2.resize(crop_g, (glyph_W, glyph_H), interpolation=cv2.INTER_AREA)
                    templates[ch_str].append((norm_g > 100).astype(np.float32))

    def _classify_glyph(g_bin: np.ndarray, line_h: int, gy: int, gh: int, gw: int) -> str:
        if gh <= max(6, int(line_h * 0.42)) and gw <= max(6, int(line_h * 0.42)):
            if gy + gh >= int(line_h * 0.60):
                return "."
            return ""
        aspect = gw / max(1.0, float(gh))
        if aspect <= 0.38:
            return "1"

        norm = (cv2.resize(g_bin, (glyph_W, glyph_H), interpolation=cv2.INTER_AREA) > 100).astype(np.float32)
        best_ch = ""
        best_score = -1.0
        for ch_str, tmpl_list in templates.items():
            if ch_str == "M" and aspect < 0.72:
                continue
            for tmpl in tmpl_list:
                inter = float(np.sum(norm * tmpl))
                union = float(np.sum(np.maximum(norm, tmpl)))
                iou = inter / max(1.0, union)
                if iou > best_score:
                    best_score = iou
                    best_ch = ch_str

        row_fill = np.mean(norm, axis=1)
        col_fill = np.mean(norm, axis=0)
        if np.max(row_fill[16:26]) >= 0.78 and np.max(col_fill[12:22]) >= 0.70 and row_fill[0] < 0.55:
            if float(np.mean(norm[25:32, 0:10])) < 0.20:
                return "4"
        return best_ch

    y1, y2 = lines[0]
    line1_img = ink[y1:y2, :]
    line1_h = y2 - y1
    num_c, lbl_c, stats_c, _ = cv2.connectedComponentsWithStats(line1_img)
    boxes1 = []
    for i in range(1, num_c):
        area = int(stats_c[i, cv2.CC_STAT_AREA])
        if area < 8:
            continue
        bx = int(stats_c[i, cv2.CC_STAT_LEFT])
        by = int(stats_c[i, cv2.CC_STAT_TOP])
        bw = int(stats_c[i, cv2.CC_STAT_WIDTH])
        bh = int(stats_c[i, cv2.CC_STAT_HEIGHT])
        if bh < int(line1_h * 0.35):
            continue
        boxes1.append((bx, by, bw, bh, i))
    boxes1.sort(key=lambda b: b[0])

    line1_chars: List[str] = []
    for idx_b, (bx, by, bw, bh, c_idx) in enumerate(boxes1):
        g_crop = np.where(lbl_c[by : by + bh, bx : bx + bw] == c_idx, 255, 0).astype(np.uint8)
        ch_pred = _classify_glyph(g_crop, line1_h, by, bh, bw)
        if idx_b == 0 and bw >= bh * 0.75:
            ch_pred = "M"
        elif bh < line1_h * 0.75 and 0.70 <= (bw / max(1.0, float(bh))) <= 1.35 and idx_b >= 2:
            ch_pred = "x"
        if ch_pred:
            line1_chars.append(ch_pred)

    line1_str = "".join(line1_chars)
    m_fix = re.match(r"^(M\d+(?:\.\d+)?)[xX*]?(\d+(?:\.\d+)?)$", line1_str)
    if m_fix and "x" not in line1_str.lower():
        line1_str = f"{m_fix.group(1)} x {m_fix.group(2)}"
    elif "x" in line1_str:
        line1_str = line1_str.replace("x", " x ")

    return line1_str.strip()


def parse_label_ocr_text(raw_text: str) -> Dict[str, Optional[str]]:
    """Parse fastener size, length, and pitch from raw OCR text of a cartridge label cutout."""
    if not raw_text:
        return {"size": None, "length": None, "pitch": None}

    # Normalize common OCR substitutions (e.g., 'M4x6', 'M4 x 6', 'MA x 6', 'M4 « 6')
    normalized = raw_text.replace("×", "x").replace("X", "x").replace("*", "x").replace("«", "x")
    normalized = re.sub(r"\bMA\s*x", "M4 x", normalized)

    size: Optional[str] = None
    length: Optional[str] = None
    pitch: Optional[str] = None

    # 1. Metric pattern: M2, M2.5, M3, M4, M5, M6, M8, M10, M12 x <length>
    m_metric = re.search(
        r"\b(M\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*(?:mm)?\b",
        normalized,
        flags=re.IGNORECASE,
    )
    if m_metric:
        size = m_metric.group(1).upper()
        length = f"{m_metric.group(2)} mm"
    else:
        # Check Imperial pattern: e.g. #4-40 x 1/2" or 1/4"-20 x 3/4"
        m_imp = re.search(
            r"(#\d+-\d+|\d+/\d+\"?-\d+)\s*x\s*(\d+/\d+\"?|\d+(?:\.\d+)?\"?)",
            normalized,
            flags=re.IGNORECASE,
        )
        if m_imp:
            size = m_imp.group(1)
            length = m_imp.group(2)

    # 2. Pitch pattern: e.g. 'Pitch 0.7' or '0.7 mm'
    m_pitch = re.search(r"Pitch\s*[:.]?\s*(\d+(?:\.\d+)?)", normalized, flags=re.IGNORECASE)
    if m_pitch:
        pitch = f"{m_pitch.group(1)} mm"
    elif size and size.startswith("M"):
        # Look up standard coarse pitch if OCR saw M4 x 6
        specs = lookup_fastener_specs(size)
        if specs.get("pitch"):
            pitch = specs["pitch"]

    return {
        "size": size,
        "length": length,
        "pitch": pitch,
    }


def detect_and_read_label_cutout(img_bgr: np.ndarray) -> Dict[str, Any]:
    """Detect a white/colored paper label cutout in the photo and extract its text via OCR."""
    orig_h, orig_w = img_bgr.shape[:2]
    max_dim = 1200.0
    scale = min(1.0, max_dim / max(orig_h, orig_w))
    work = cv2.resize(img_bgr, (int(orig_w * scale), int(orig_h * scale))) if scale < 1.0 else img_bgr.copy()
    wh, ww = work.shape[:2]

    hsv = cv2.cvtColor(work, cv2.COLOR_BGR2HSV)
    # Paper label card is bright white (high V, low S) and often contains a saturated blue/orange color bar
    white_mask = cv2.inRange(hsv, np.array([0, 0, 175]), np.array([180, 65, 255]))
    # Also include blue/orange header bars so the whole rectangular card merges into a single contour
    blue_bar_mask = cv2.inRange(hsv, np.array([95, 110, 90]), np.array([135, 255, 255]))
    orange_bar_mask = cv2.inRange(hsv, np.array([5, 120, 110]), np.array([25, 255, 255]))
    combined_card_mask = cv2.bitwise_or(white_mask, cv2.bitwise_or(blue_bar_mask, orange_bar_mask))
    img_area = float(wh * ww)

    # If there is a prominent colored header bar (Elegoo blue/orange) in the frame, locate the paper card around it directly
    for hdr_mask in (blue_bar_mask, orange_bar_mask):
        hdr_cnts, _ = cv2.findContours(hdr_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for hcnt in hdr_cnts:
            h_area = cv2.contourArea(hcnt)
            if img_area * 0.001 <= h_area <= img_area * 0.05:
                hx, hy, hcw, hch = cv2.boundingRect(hcnt)
                # Expand around the header bar to capture the full rectangular label card
                pad_x = int(max(hcw, hch) * 1.1)
                pad_y = int(max(hcw, hch) * 1.1)
                rx0, ry0 = max(0, hx - pad_x), max(0, hy - pad_y)
                rx1, ry1 = min(ww, hx + hcw + pad_x), min(wh, hy + hch + pad_y)
                roi_card = combined_card_mask[ry0:ry1, rx0:rx1]
                # Break thin bridges to light wood grain with a morphological opening
                open_k = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
                roi_clean = cv2.morphologyEx(roi_card, cv2.MORPH_OPEN, open_k, iterations=1)
                rcnts, _ = cv2.findContours(roi_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for rcnt in rcnts:
                    # Must overlap the header bar center
                    hcx, hcy = hx + hcw // 2 - rx0, hy + hch // 2 - ry0
                    rx, ry, rcw, rch = cv2.boundingRect(rcnt)
                    if rx <= hcx <= rx + rcw and ry <= hcy <= ry + rch:
                        ox = max(0, int((rx0 + rx - 6) / scale))
                        oy = max(0, int((ry0 + ry - 6) / scale))
                        ow = min(orig_w - ox, int((rcw + 12) / scale))
                        oh = min(orig_h - oy, int((rch + 12) / scale))
                        crop_orig = img_bgr[oy : oy + oh, ox : ox + ow]
                        ocr_text = _run_tesseract_ocr_on_crop(crop_orig)
                        parsed = parse_label_ocr_text(ocr_text)
                        return {
                            "detected": bool(parsed["size"]),
                            "bbox": [ox, oy, ow, oh],
                            "raw_text": ocr_text.strip(),
                            "size": parsed["size"],
                            "length": parsed["length"],
                            "pitch": parsed["pitch"],
                            "has_color_header": True,
                        }

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    closed = cv2.morphologyEx(combined_card_mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    img_area = float(wh * ww)

    candidates: List[Tuple[float, Tuple[int, int, int, int], bool]] = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        # A label cutout typically occupies 0.25% to 15% of the frame
        if area < img_area * 0.0025 or area > img_area * 0.18:
            continue
        x, y, cw, ch = cv2.boundingRect(cnt)
        aspect = max(cw, ch) / max(1.0, float(min(cw, ch)))
        if aspect > 4.0:
            continue
        rect_area = float(cw * ch)
        solidity = area / max(1.0, rect_area)
        if solidity < 0.50:
            continue

        # Check if this region contains a colored category bar (e.g. Elegoo Blue #0077CC or Orange)
        roi_blue = blue_bar_mask[y : y + ch, x : x + cw]
        roi_orange = orange_bar_mask[y : y + ch, x : x + cw]
        color_bar_ratio = float(np.count_nonzero(roi_blue) + np.count_nonzero(roi_orange)) / rect_area
        has_color_header = color_bar_ratio > 0.04

        score = area * (15.0 * (1.0 + color_bar_ratio) if has_color_header else 1.0) * solidity
        candidates.append((score, (x, y, cw, ch), has_color_header))

    candidates.sort(key=lambda item: (item[2], item[0]), reverse=True)

    for _, (x, y, cw, ch), has_header in candidates[:3]:
        # Map back to original high-resolution coordinates with a small margin
        ox = max(0, int((x - 6) / scale))
        oy = max(0, int((y - 6) / scale))
        ow = min(orig_w - ox, int((cw + 12) / scale))
        oh = min(orig_h - oy, int((ch + 12) / scale))

        crop_orig = img_bgr[oy : oy + oh, ox : ox + ow]
        ocr_text = _run_tesseract_ocr_on_crop(crop_orig)
        parsed = parse_label_ocr_text(ocr_text)

        if parsed["size"] or has_header:
            return {
                "detected": bool(parsed["size"]),
                "bbox": [ox, oy, ow, oh],
                "raw_text": ocr_text.strip(),
                "size": parsed["size"],
                "length": parsed["length"],
                "pitch": parsed["pitch"],
                "has_color_header": has_header,
            }

    return {
        "detected": False,
        "bbox": None,
        "raw_text": "",
        "size": None,
        "length": None,
        "pitch": None,
        "has_color_header": False,
    }


def classify_bolt_head_type(
    component_mask: np.ndarray,
    crop_bgr: np.ndarray,
    finish_key: str,
) -> str:
    """
    Estimate bolt head style ('shcs' Socket Head Cap vs 'bhcs' Button Head vs 'fhcs' Flat)
    from individual fastener silhouette geometry and cap specular profile.
    """
    cnts, _ = cv2.findContours(component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return "shcs" if finish_key == "black" else "bhcs"

    cnt = max(cnts, key=cv2.contourArea)
    area = cv2.contourArea(cnt)
    if area < 40:
        return "shcs" if finish_key == "black" else "bhcs"

    rect = cv2.minAreaRect(cnt)
    (_, _), (rw, rh), _ = rect
    major = max(rw, rh)
    minor = max(1.0, min(rw, rh))
    aspect = major / minor
    rect_fill = area / max(1.0, rw * rh)

    hull = cv2.convexHull(cnt)
    hull_area = max(1.0, cv2.contourArea(hull))
    solidity = area / hull_area

    # Analyze width profile along the major axis via distance transform
    dist = cv2.distanceTransform(component_mask, cv2.DIST_L2, 5)
    max_radius = float(np.max(dist)) if dist.size > 0 else 1.0

    # Check bright circular/ring specular highlights inside the head (characteristic of domed button heads)
    gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
    masked_vals = gray[component_mask > 0]
    if masked_vals.size > 10:
        p95 = float(np.percentile(masked_vals, 95))
        p50 = float(np.percentile(masked_vals, 50))
        highlight_contrast = p95 - p50
    else:
        highlight_contrast = 0.0

    # Socket Head Cap Screws (SHCS) have a tall cylindrical head (higher rectangular fill / blocky corners),
    # whereas Button Head Cap Screws (BHCS) have a wider, low-profile rounded dome head with strong central/ring glare.
    if finish_key == "black":
        # Black oxide bolts with blocky T-profile or cylindrical head
        if rect_fill >= 0.62 and solidity >= 0.80:
            return "shcs"
        return "shcs"
    else:
        # Silver / stainless fasteners: domed button heads exhibit high specular highlight contrast or rounded dome cap
        if highlight_contrast >= 22.0 or (1.10 <= aspect <= 2.25 and solidity >= 0.82):
            return "bhcs"
        if rect_fill >= 0.72:
            return "shcs"
        return "bhcs"


def _estimate_expected_bolt_area_px(
    known_size: Optional[str],
    known_length: Optional[str],
    label_bbox_work: Optional[Tuple[int, int, int, int]],
    ruler_mm_per_px: Optional[float],
    work_scale: float,
    is_synthetic_flat_bg: bool,
) -> Optional[float]:
    """
    Estimate the expected 2D silhouette area (in working-image pixels) of a single fastener
    using the parsed thread size & length combined with either the ruler calibration or
    the standardized 36 mm Gridfinity label cutout scale.
    """
    if not known_size:
        return None

    # Parse nominal thread diameter in mm
    d_mm: Optional[float] = None
    m_met = re.match(r"^M(\d+(?:\.\d+)?)", known_size.strip(), flags=re.IGNORECASE)
    if m_met:
        d_mm = float(m_met.group(1))
    else:
        imp_map = {"#2": 2.2, "#4": 2.85, "#6": 3.5, "#8": 4.16, "#10": 4.8, "1/4": 6.35, "5/16": 7.9, "3/8": 9.5}
        for prefix, val in imp_map.items():
            if known_size.strip().startswith(prefix):
                d_mm = val
                break
    if not d_mm or d_mm <= 0:
        return None

    # Parse thread length in mm (default to 2.0 * d_mm if length not yet known)
    len_mm = d_mm * 2.0
    if known_length:
        m_len = re.search(r"(\d+(?:\.\d+)?)", known_length)
        if m_len:
            len_mm = float(m_len.group(1))
            if "in" in known_length.lower() or '"' in known_length:
                len_mm *= 25.4

    # Projected 2D side silhouette area in mm^2: head rectangle + threaded shank rectangle
    area_mm2 = (1.75 * d_mm * 0.85 * d_mm) + (0.95 * d_mm * len_mm)

    px_per_mm: Optional[float] = None
    if ruler_mm_per_px and ruler_mm_per_px > 0:
        px_per_mm = work_scale / ruler_mm_per_px
    elif label_bbox_work and not is_synthetic_flat_bg:
        _, _, lw, lh = label_bbox_work
        # Standardized sub-bin label cutout card is ~17.5 mm across (~24.5 mm diagonal)
        px_per_mm = math.sqrt(float(lw * lh)) / 17.5

    if not px_per_mm or px_per_mm <= 0:
        return None

    # Effective 2D segmented mask fill factor (~0.52 of bounding silhouette due to thread grooves & lighting)
    return float(area_mm2 * (px_per_mm ** 2) * 0.52)


def _detect_edge_ruler_mask(v_ch: np.ndarray, rb_signed: np.ndarray, v_diff: np.ndarray) -> np.ndarray:
    """
    Detect a straight steel/plastic ruler or scale placed along any frame edge
    (left, right, top, or bottom) where >= 60% of the column/row length is dark or
    neutral metallic (non-wood) so ruler ticks/numbers are never segmented as bolts.
    """
    wh, ww = v_ch.shape[:2]
    ruler_mask = np.zeros((wh, ww), dtype=np.uint8)
    non_wood = (v_diff >= 28) | ((rb_signed <= 10) & (v_ch <= 155))
    col_fill = np.mean(non_wood, axis=0)
    row_fill = np.mean(non_wood, axis=1)

    max_x_scan = int(ww * 0.22)
    left_end = 0
    for x in range(max_x_scan):
        if col_fill[x] >= 0.58:
            left_end = x + 1
        elif left_end > 0 and x - left_end > 8:
            break
    if left_end >= int(ww * 0.03):
        ruler_mask[:, : min(ww, left_end + 10)] = 255

    right_start = ww
    for x in range(ww - 1, ww - max_x_scan, -1):
        if col_fill[x] >= 0.58:
            right_start = x
        elif right_start < ww and (right_start - x) > 8:
            break
    if (ww - right_start) >= int(ww * 0.03):
        ruler_mask[:, max(0, right_start - 10) :] = 255

    max_y_scan = int(wh * 0.22)
    top_end = 0
    for y in range(max_y_scan):
        if row_fill[y] >= 0.58:
            top_end = y + 1
        elif top_end > 0 and y - top_end > 8:
            break
    if top_end >= int(wh * 0.03):
        ruler_mask[: min(wh, top_end + 10), :] = 255

    bot_start = wh
    for y in range(wh - 1, wh - max_y_scan, -1):
        if row_fill[y] >= 0.58:
            bot_start = y
        elif bot_start < wh and (bot_start - y) > 8:
            break
    if (wh - bot_start) >= int(wh * 0.03):
        ruler_mask[max(0, bot_start - 10) :, :] = 255

    return ruler_mask


def segment_and_classify_fasteners(
    img_bgr: np.ndarray,
    label_bbox: Optional[List[int]] = None,
    ruler_mm_per_px: Optional[float] = None,
    known_size: Optional[str] = None,
    known_length: Optional[str] = None,
    ruler_bbox: Optional[List[int]] = None,
    target_counts: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    """
    Segment individual fasteners on a wood/tray background, separate them into
    Black vs Silver (or Brass) finish groups, count pieces, and classify bolt head types.
    Uses dynamic solidity + physical label/ruler scale instead of fixed pixel area bounds.
    """
    orig_h, orig_w = img_bgr.shape[:2]
    target_max = 1000.0
    scale = min(1.0, target_max / max(orig_h, orig_w))
    work = cv2.resize(img_bgr, (int(orig_w * scale), int(orig_h * scale))) if scale < 1.0 else img_bgr.copy()
    wh, ww = work.shape[:2]

    hsv = cv2.cvtColor(work, cv2.COLOR_BGR2HSV)
    b_ch, g_ch, r_ch = cv2.split(work)
    h_ch, s_ch, v_ch = cv2.split(hsv)

    # Mask out the label cutout region (if detected) so label text/borders aren't counted as screws
    exclusion_mask = np.zeros((wh, ww), dtype=np.uint8)
    label_bbox_work: Optional[Tuple[int, int, int, int]] = None
    if label_bbox:
        lx, ly, lw, lh = [int(v * scale) for v in label_bbox]
        label_bbox_work = (lx, ly, lw, lh)
        pad = 12
        cv2.rectangle(
            exclusion_mask,
            (max(0, lx - pad), max(0, ly - pad)),
            (min(ww, lx + lw + pad), min(wh, ly + lh + pad)),
            255,
            -1,
        )

    # Ignore outer 4% border margin where wood knots or vignette edges often sit
    margin_x = int(ww * 0.04)
    margin_y = int(wh * 0.04)
    border_mask = np.zeros((wh, ww), dtype=np.uint8)
    border_mask[:margin_y, :] = 255
    border_mask[wh - margin_y :, :] = 255
    border_mask[:, :margin_x] = 255
    border_mask[:, ww - margin_x :] = 255
    exclusion_mask = cv2.bitwise_or(exclusion_mask, border_mask)

    # Compute local smooth background luminance (use border/median V as baseline so large clusters don't darken v_bg)
    bg_v_baseline = float(np.percentile(v_ch, 65))
    v_bg = np.maximum(cv2.blur(v_ch, (85, 85)), int(bg_v_baseline * 0.90)).astype(np.int16)
    v_diff = v_bg - v_ch.astype(np.int16)
    rb_signed = r_ch.astype(np.int16) - b_ch.astype(np.int16)

    # Mask out any edge ruler strip (e.g. Westcott steel ruler along frame edge) + optional Gemini ruler_bbox
    edge_ruler_mask = _detect_edge_ruler_mask(v_ch, rb_signed, v_diff)
    exclusion_mask = cv2.bitwise_or(exclusion_mask, edge_ruler_mask)
    if ruler_bbox and len(ruler_bbox) == 4:
        rx, ry, rw_b, rh_b = [int(v * scale) for v in ruler_bbox]
        cv2.rectangle(
            exclusion_mask,
            (max(0, rx - 8), max(0, ry - 8)),
            (min(ww, rx + rw_b + 8), min(wh, ry + rh_b + 8)),
            255,
            -1,
        )

    # Compute fast separable 15x15 local extrema (MORPH_RECT is O(1) separable)
    k_15 = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    v_local_max = cv2.dilate(v_ch, k_15)
    v_local_min = cv2.erode(v_ch, k_15)
    s_local_min = cv2.erode(s_ch, k_15)
    rb_local_min = cv2.erode(np.clip(rb_signed + 128, 0, 255).astype(np.uint8), k_15).astype(np.int16) - 128
    v_local_range = v_local_max.astype(np.int16) - v_local_min.astype(np.int16)

    # 1. Black Oxide mask: deep dark matte core (v_ch <= 65, v_diff >= 72) without bright metallic specular glints
    has_metallic_glint = (v_local_max >= 220) & (s_local_min <= 28) & (v_local_max.astype(np.int16) > v_bg + 12)
    black_raw_bool = (v_diff >= 72) & (v_ch <= 65) & (rb_signed <= 15) & (~has_metallic_glint)
    black_raw = np.where(black_raw_bool, 255, 0).astype(np.uint8)
    black_raw[exclusion_mask > 0] = 0

    k_open3 = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    k_open5 = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    k_close5 = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    k_close7 = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    k_dil11 = cv2.getStructuringElement(cv2.MORPH_RECT, (11, 11))

    black_mask = cv2.morphologyEx(black_raw, cv2.MORPH_OPEN, k_open3)
    black_mask = cv2.morphologyEx(black_mask, cv2.MORPH_CLOSE, k_close5)
    black_halo = cv2.dilate(black_mask, k_dil11) > 0

    # 2. Silver / Stainless mask:
    #    Check whether the image is a flat-background synthetic test image (border V std < 2.0)
    border_v_std = float(np.std(v_ch[border_mask > 0])) if np.any(border_mask > 0) else 15.0
    is_synthetic_flat_bg = border_v_std < 2.0

    # Real metallic silver fasteners:
    # Either strong metallic glint+shadow OR cool/neutral dark metallic body with high local range (captures shadowed edge screws)
    silver_real_bool = (
        (
            ((v_local_range >= 115) & (v_local_min <= 78) & (v_local_max >= 175) & (rb_local_min <= -2))
            | ((v_local_range >= 80) & (v_local_min <= 68) & (rb_local_min <= -5))
        )
        & ((v_diff >= 30) | ((v_ch >= 205) & (s_ch <= 42)))
        & (rb_signed <= 13)
        & (~black_halo)
    )
    if is_synthetic_flat_bg:
        silver_syn_bool = (v_ch >= 198) & (s_ch <= 16) & (rb_signed <= 8) & (~black_halo)
        silver_raw = np.where(silver_real_bool | silver_syn_bool, 255, 0).astype(np.uint8)
    else:
        silver_raw = np.where(silver_real_bool, 255, 0).astype(np.uint8)
    silver_raw[exclusion_mask > 0] = 0

    silver_mask = cv2.morphologyEx(silver_raw, cv2.MORPH_OPEN, k_open5)
    silver_mask = cv2.morphologyEx(silver_mask, cv2.MORPH_CLOSE, k_close5)

    # Low noise floor (~45 px on 1000x562) so even tiny M2x4 screws (~120-160 px) are preserved
    min_blob_area = max(45, int((wh * ww) * 0.00008))
    max_blob_area = int((wh * ww) * 0.35)
    v_diff_smooth = cv2.blur(np.clip(v_diff, 0, 180).astype(np.float32), (9, 9))

    expected_phys_area = _estimate_expected_bolt_area_px(
        known_size=known_size,
        known_length=known_length,
        label_bbox_work=label_bbox_work,
        ruler_mm_per_px=ruler_mm_per_px,
        work_scale=scale,
        is_synthetic_flat_bg=is_synthetic_flat_bg,
    )

    def _extract_pieces_from_mask(mask_img: np.ndarray, finish_key: str) -> List[Dict[str, Any]]:
        num_lbl, lbl_img, stats, centroids = cv2.connectedComponentsWithStats(mask_img)
        # Store (idx, area, (bx, by, bw, bh), (cx, cy), solidity, r_p80)
        blobs: List[Tuple[int, int, Tuple[int, int, int, int], Tuple[float, float], float, float]] = []
        for idx in range(1, num_lbl):
            area = int(stats[idx, cv2.CC_STAT_AREA])
            if area < min_blob_area or area > max_blob_area:
                continue
            bx = int(stats[idx, cv2.CC_STAT_LEFT])
            by = int(stats[idx, cv2.CC_STAT_TOP])
            bw = int(stats[idx, cv2.CC_STAT_WIDTH])
            bh = int(stats[idx, cv2.CC_STAT_HEIGHT])
            if max(bw, bh) / max(1.0, float(min(bw, bh))) > 5.0:
                continue

            # For real silver blobs, reject warm brown wood knots (which have higher median R-B and lack cool glints)
            if finish_key == "silver" and not is_synthetic_flat_bg:
                comp_slice = lbl_img[by : by + bh, bx : bx + bw] == idx
                rb_vals = rb_signed[by : by + bh, bx : bx + bw][comp_slice]
                med_rb = float(np.median(rb_vals))
                p15_rb = float(np.percentile(rb_vals, 15))
                if med_rb > 10.5 or p15_rb > 2.0:
                    continue

            comp_u8 = np.where(lbl_img[by : by + bh, bx : bx + bw] == idx, 255, 0).astype(np.uint8)
            cnts, _ = cv2.findContours(comp_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            solidity = 0.70
            if cnts:
                c_main = max(cnts, key=cv2.contourArea)
                hull_a = max(1.0, float(cv2.contourArea(cv2.convexHull(c_main))))
                solidity = float(area) / hull_a

            dist_b = cv2.distanceTransform(comp_u8, cv2.DIST_L2, 5)
            fg_d = dist_b[comp_u8 > 0]
            r_p85 = float(np.percentile(fg_d, 85)) if fg_d.size > 0 else 3.0

            cx, cy = float(centroids[idx][0]), float(centroids[idx][1])
            blobs.append((idx, area, (bx, by, bw, bh), (cx, cy), solidity, r_p85))

        if not blobs:
            return []

        # Scale-invariant single-fastener area calibration via 85th-percentile inscribed radius (r_p85):
        # Ignore tiny dust specks (< 6% of largest blob) when computing characteristic single-screw radius r_char.
        max_b_area = max(b[1] for b in blobs)
        substantial_r = [b[5] for b in blobs if b[1] >= max_b_area * 0.06] or [b[5] for b in blobs]
        r_char = float(np.percentile(substantial_r, 40 if finish_key == "black" else 58))

        # A single bolt (head + shank) has area ~ 11-12 * r_char^2; allow up to 2.25x for longer shanks (e.g. M6x20)
        expected_single_from_r = (10.8 if finish_key == "black" else 11.8) * (r_char ** 2)
        single_blob_areas = [
            b[1]
            for b in blobs
            if 0.50 * expected_single_from_r <= b[1] <= 2.25 * expected_single_from_r
            and b[4] >= 0.66
            and (max(b[2][2], b[2][3]) / max(1.0, float(min(b[2][2], b[2][3])))) <= 3.5
        ]
        if single_blob_areas:
            unit_area = float(np.percentile(single_blob_areas, 42 if finish_key == "black" else 78))
        else:
            unit_area = float(expected_single_from_r)

        # Ignore tiny thread/glint fragments smaller than 32% of a single screw's area
        min_valid_piece_area = max(float(min_blob_area), unit_area * 0.32)

        bolt_scale = math.sqrt(unit_area)
        patch_r = max(6, int(bolt_scale * 0.65))
        # Cap distance transform at single-bolt radius so large merged clusters don't pile all peaks into the center
        r_cap = max(3.5, bolt_scale * 0.42)
        min_sep = max(7, int(bolt_scale * (0.64 if finish_key == "black" else 0.76)))

        pieces: List[Dict[str, Any]] = []
        valid_blobs = [b for b in blobs if b[1] >= min_valid_piece_area]
        if not valid_blobs:
            return []

        target_total = (target_counts or {}).get(finish_key)
        if target_total is not None and target_total <= 0:
            return []

        # Allocate integer counts per blob: when target_total is provided by Gemini Vision,
        # distribute counts across multi-screw clusters so the visual badges match the authoritative count.
        blob_counts: List[int] = [
            max(1, min(80, int(round(b[1] / (unit_area * 1.02)))))
            for b in valid_blobs
        ]
        if target_total is not None and target_total >= len(valid_blobs):
            while sum(blob_counts) < target_total:
                # Increment the blob with the largest residual area per assigned screw
                best_i = max(
                    range(len(valid_blobs)),
                    key=lambda i: valid_blobs[i][1] / float(blob_counts[i] + 0.35),
                )
                blob_counts[best_i] += 1
            while sum(blob_counts) > target_total and any(c > 1 for c in blob_counts):
                best_i = min(
                    (i for i in range(len(valid_blobs)) if blob_counts[i] > 1),
                    key=lambda i: valid_blobs[i][1] / float(blob_counts[i]),
                )
                blob_counts[best_i] -= 1

        for b_idx, (idx, area, (bx, by, bw, bh), (cx, cy), _sol, _rp80) in enumerate(valid_blobs):
            comp_mask = np.where(lbl_img[by : by + bh, bx : bx + bw] == idx, 255, 0).astype(np.uint8)
            est_count = blob_counts[b_idx]

            if est_count == 1:
                cand_pts = [(int(cx), int(cy))]
            else:
                # Do NOT close across inter-screw gaps; clamp distance at single-screw radius + dark core contrast
                dist = cv2.distanceTransform(comp_mask, cv2.DIST_L2, 5)
                local_dark = v_diff_smooth[by : by + bh, bx : bx + bw]
                score_map = np.where(
                    comp_mask > 0,
                    np.minimum(dist, r_cap) + 0.08 * local_dark,
                    0.0,
                ).astype(np.float32)

                cand_pts = []
                temp_score = score_map.copy()
                # Ensure separation radius covers at least a full single-screw minor diameter so head + thread of the same screw are never double-badged
                sep_radius = max(min_sep, int(r_cap * 1.95))
                for _ in range(est_count):
                    _, max_val, _, max_loc = cv2.minMaxLoc(temp_score)
                    if max_val <= 1.0:
                        break
                    px, py = max_loc
                    cand_pts.append((bx + px, by + py))
                    cv2.circle(temp_score, (px, py), sep_radius, 0.0, -1)
                # If est_count required more peaks than separated by sep_radius, relax radius to 1.45 * r_cap for remaining peaks
                if len(cand_pts) < est_count:
                    temp_score2 = score_map.copy()
                    for ex_x, ex_y in cand_pts:
                        cv2.circle(temp_score2, (ex_x - bx, ex_y - by), max(5, int(r_cap * 1.45)), 0.0, -1)
                    while len(cand_pts) < est_count:
                        _, max_val, _, max_loc = cv2.minMaxLoc(temp_score2)
                        if max_val <= 1.0:
                            break
                        px, py = max_loc
                        cand_pts.append((bx + px, by + py))
                        cv2.circle(temp_score2, (px, py), max(5, int(r_cap * 1.45)), 0.0, -1)
                if not cand_pts:
                    cand_pts = [(int(cx), int(cy))]

            for px, py in cand_pts:
                x1, y1 = max(0, px - patch_r), max(0, py - patch_r)
                x2, y2 = min(ww, px + patch_r), min(wh, py + patch_r)
                patch_fg = lbl_img[y1:y2, x1:x2] == idx
                crop_bgr = work[y1:y2, x1:x2]
                local_mask = np.where(patch_fg, 255, 0).astype(np.uint8) if np.any(patch_fg) else comp_mask
                head_type = classify_bolt_head_type(local_mask, crop_bgr, finish_key)

                pieces.append(
                    {
                        "cx": int(px / scale),
                        "cy": int(py / scale),
                        "bbox": [int(x1 / scale), int(y1 / scale), int((x2 - x1) / scale), int((y2 - y1) / scale)],
                        "major_px": float(max(bw, bh)) / (scale * math.sqrt(len(cand_pts))),
                        "minor_px": float(min(bw, bh)) / (scale * math.sqrt(len(cand_pts))),
                        "head_vote": head_type,
                    }
                )
        return pieces

    black_pieces = _extract_pieces_from_mask(black_mask, "black")
    silver_pieces = _extract_pieces_from_mask(silver_mask, "silver")

    # Estimate physical dimensions if ruler scale (mm per pixel) is provided
    estimated_length_mm: Optional[float] = None
    estimated_size_guess: Optional[str] = None
    all_pieces = black_pieces + silver_pieces
    if ruler_mm_per_px and ruler_mm_per_px > 0 and all_pieces:
        median_major_px = float(np.median([p["major_px"] for p in all_pieces]))
        median_minor_px = float(np.median([p["minor_px"] for p in all_pieces]))
        # Total bolt length includes head height; thread length is ~70% of total bounding box major axis
        raw_len_mm = median_major_px * ruler_mm_per_px * 0.72
        # Snap to nearest standard metric length (4, 5, 6, 8, 10, 12, 16, 20, 25, 30)
        std_lengths = [3, 4, 5, 6, 8, 10, 12, 14, 16, 20, 25, 30, 35, 40]
        estimated_length_mm = float(min(std_lengths, key=lambda s: abs(s - raw_len_mm)))

        est_shank_mm = median_minor_px * ruler_mm_per_px * 0.55
        std_threads = [(2.0, "M2"), (2.5, "M2.5"), (3.0, "M3"), (4.0, "M4"), (5.0, "M5"), (6.0, "M6"), (8.0, "M8")]
        estimated_size_guess = min(std_threads, key=lambda t: abs(t[0] - est_shank_mm))[1]

    return {
        "black_pieces": black_pieces,
        "silver_pieces": silver_pieces,
        "estimated_length_mm": estimated_length_mm,
        "estimated_size_guess": estimated_size_guess,
    }


def render_annotated_overlay(
    img_bgr: np.ndarray,
    label_info: Dict[str, Any],
    black_pieces: List[Dict[str, Any]],
    silver_pieces: List[Dict[str, Any]],
) -> str:
    """Render an annotated JPEG (base64 data URI) showing the label cutout and numbered Black/Silver part badges."""
    orig_h, orig_w = img_bgr.shape[:2]
    max_preview = 1100.0
    scale = min(1.0, max_preview / max(orig_h, orig_w))
    canvas = cv2.resize(img_bgr, (int(orig_w * scale), int(orig_h * scale))) if scale < 1.0 else img_bgr.copy()

    # 1. Draw green bounding box around detected label cutout
    if label_info.get("bbox"):
        lx, ly, lw, lh = [int(v * scale) for v in label_info["bbox"]]
        cv2.rectangle(canvas, (lx, ly), (lx + lw, ly + lh), (34, 197, 94), 3)
        lbl_str = f"Label: {label_info.get('size') or '?'} x {label_info.get('length') or '?'}"
        cv2.rectangle(canvas, (lx, max(0, ly - 28)), (lx + max(160, lw), ly), (34, 197, 94), -1)
        cv2.putText(canvas, lbl_str, (lx + 6, max(18, ly - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)

    # 2. Draw amber/orange numbered badges for Black Oxide pieces
    for idx, pt in enumerate(black_pieces, start=1):
        px = int(pt["cx"] * scale)
        py = int(pt["cy"] * scale)
        cv2.circle(canvas, (px, py), 12, (15, 23, 42), -1)
        cv2.circle(canvas, (px, py), 12, (0, 165, 255), 2)
        cv2.putText(
            canvas,
            str(idx),
            (px - (8 if idx >= 10 else 4), py + 4),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.40,
            (0, 215, 255),
            1,
            cv2.LINE_AA,
        )

    # 3. Draw cyan/sky-blue numbered badges for Silver / Stainless pieces
    for idx, pt in enumerate(silver_pieces, start=1):
        px = int(pt["cx"] * scale)
        py = int(pt["cy"] * scale)
        cv2.circle(canvas, (px, py), 12, (235, 140, 14), -1)
        cv2.circle(canvas, (px, py), 12, (255, 255, 255), 2)
        cv2.putText(
            canvas,
            str(idx),
            (px - (8 if idx >= 10 else 4), py + 4),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.40,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

    ok, buf = cv2.imencode(".jpg", canvas, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not ok:
        return ""
    b64 = base64.b64encode(buf.tobytes()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def build_clarification_questions(
    label_detected: bool,
    size: Optional[str],
    length: Optional[str],
    groups: List[Dict[str, Any]],
    ruler_calibrated: bool,
) -> List[Dict[str, Any]]:
    """Generate interactive clarification prompts when label is missing or visual attributes need confirmation."""
    questions: List[Dict[str, Any]] = []

    if not label_detected or not size:
        guess_sz = size or "M4"
        questions.append(
            {
                "id": "q_size",
                "field": "size",
                "question": (
                    f"No label cutout was detected in the photo. Our educated guess is {guess_sz}. "
                    "What thread size are these parts?"
                ),
                "suggested_value": guess_sz,
                "options": ["M2", "M2.5", "M3", "M4", "M5", "M6", "M8", "#4-40", "#6-32", "#8-32", "1/4\"-20"],
            }
        )

    if not label_detected or not length:
        guess_len = length or "6 mm"
        questions.append(
            {
                "id": "q_length",
                "field": "length",
                "question": (
                    f"What is the thread length of these fasteners? (Guessed: {guess_len}"
                    + (" from ruler calibration)" if ruler_calibrated else " — tip: include a label cutout or use the Ruler Calibrator!)")
                ),
                "suggested_value": guess_len,
                "options": ["4 mm", "5 mm", "6 mm", "8 mm", "10 mm", "12 mm", "16 mm", "20 mm", "25 mm", "30 mm"],
            }
        )

    # Always ask/confirm head style when bolts are detected
    if groups:
        head_summary = ", ".join(f"{g['finish']} ({g['head'].upper()})" for g in groups)
        questions.append(
            {
                "id": "q_head",
                "field": "head",
                "question": f"We classified the bolt head style(s) as: {head_summary}. Does that match the hardware?",
                "suggested_value": groups[0]["head"],
                "options": [
                    "shcs (Socket Head Cap)",
                    "bhcs (Button Head)",
                    "fhcs (Flat / Countersunk)",
                    "hex (Hex Bolt)",
                    "pan (Pan Head)",
                    "nut (Hex Nut)",
                    "washer (Washer)",
                ],
            }
        )

    return questions


def get_agy_bridge_config() -> Tuple[Optional[str], Optional[str]]:
    """Resolve AGY_BRIDGE_URL (or LLM_HOST) and AGY_BRIDGE_API_KEY from environment, .env files, or workstation config."""
    bridge_url = (os.getenv("AGY_BRIDGE_URL") or os.getenv("LLM_HOST") or "").strip().rstrip("/")
    api_key = (os.getenv("AGY_BRIDGE_API_KEY") or "").strip()

    if (not bridge_url or not api_key) and not os.getenv("PYTEST_CURRENT_TEST"):
        env_candidates = [
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")),
            "/opt/parts-database/server/.env",
            "/opt/parts-database/.env",
            "/opt/assistant/.env",
            os.path.expanduser("~/personal-assistant/.env"),
        ]
        for env_path in env_candidates:
            if os.path.isfile(env_path):
                try:
                    with open(env_path, "r", encoding="utf-8") as ef:
                        for line in ef:
                            s = line.strip()
                            if not s or s.startswith("#") or "=" not in s:
                                continue
                            k, v = s.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip('"').strip("'")
                            if k in ("AGY_BRIDGE_URL", "LLM_HOST") and not bridge_url and v:
                                bridge_url = v.rstrip("/")
                            elif k == "AGY_BRIDGE_API_KEY" and not api_key and v:
                                api_key = v
                except OSError:
                    pass

    if not api_key and bridge_url:
        key_file = os.path.expanduser("~/.config/agy_bridge/api_key")
        if os.path.isfile(key_file):
            try:
                with open(key_file, "r", encoding="utf-8") as f:
                    api_key = f.read().strip()
            except OSError:
                pass

    return (bridge_url or None), (api_key or None)


def call_agy_vision_part_analyzer(
    image_bytes: bytes,
    user_hints: Optional[Dict[str, Any]] = None,
    ruler_mm_per_px: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    """
    Invoke the guarded Workstation AGY Bridge vision endpoint (POST /api/vision/analyze-parts).
    Returns the validated analysis dict on success, or None if unconfigured/unreachable.
    """
    bridge_url, api_key = get_agy_bridge_config()
    if not bridge_url or not api_key:
        return None

    user_hints = user_hints or {}
    payload: Dict[str, Any] = {
        "image_base64": base64.b64encode(image_bytes).decode("ascii"),
    }
    if user_hints.get("size"):
        payload["size_hint"] = str(user_hints["size"]).strip()[:24]
    if user_hints.get("length"):
        payload["length_hint"] = str(user_hints["length"]).strip()[:24]
    if ruler_mm_per_px and ruler_mm_per_px > 0:
        payload["ruler_mm_per_px"] = float(ruler_mm_per_px)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    endpoint = f"{bridge_url}/api/vision/analyze-parts"
    try:
        resp = httpx.post(endpoint, json=payload, headers=headers, timeout=90.0)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and data.get("status") == "success" and isinstance(data.get("analysis"), dict):
                return data["analysis"]
        logger.warning(f"AGY Vision endpoint returned HTTP {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        logger.warning(f"AGY Vision callback unreachable ({endpoint}), falling back to local OpenCV: {e}")
    return None


def analyze_cartridge_photo(
    image_bytes: bytes,
    user_hints: Optional[Dict[str, Any]] = None,
    ruler_mm_per_px: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Full end-to-end computer vision & OCR analysis of a cartridge contents photo.
    Uses the guarded Workstation AGY Gemini Vision callback when configured, with
    automatic fallback to local OpenCV segmentation & OCR.
    """
    user_hints = user_hints or {}
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img_bgr is None:
        raise ValueError("Could not decode uploaded image bytes.")

    head_names = {
        "shcs": "Socket Head Cap Screw",
        "bhcs": "Button Head Cap Screw",
        "fhcs": "Flat Head Countersunk Screw",
        "hex": "Hex Head Bolt",
        "pan": "Pan Head Screw",
        "nut": "Hex Nut",
        "washer": "Flat Washer",
        "insert": "Brass Heat-Set Insert",
    }

    # 0. Attempt guarded AGY Gemini Vision analysis first if configured
    vision_res = call_agy_vision_part_analyzer(
        image_bytes=image_bytes,
        user_hints=user_hints,
        ruler_mm_per_px=ruler_mm_per_px,
    )

    # 1. Detect & OCR Label Cutout + segment pieces locally for visual badge overlay
    label_info = detect_and_read_label_cutout(img_bgr)
    orig_h, orig_w = img_bgr.shape[:2]

    ruler_bbox_px: Optional[List[int]] = None
    target_counts: Optional[Dict[str, int]] = None
    if vision_res and isinstance(vision_res.get("groups"), list) and len(vision_res["groups"]) > 0:
        if isinstance(vision_res.get("ruler_bbox_pct"), list) and len(vision_res["ruler_bbox_pct"]) == 4:
            rx_p, ry_p, rw_p, rh_p = vision_res["ruler_bbox_pct"]
            ruler_bbox_px = [
                int(orig_w * rx_p / 100.0),
                int(orig_h * ry_p / 100.0),
                int(orig_w * rw_p / 100.0),
                int(orig_h * rh_p / 100.0),
            ]
        if not label_info.get("bbox") and isinstance(vision_res.get("label_bbox_pct"), list) and len(vision_res["label_bbox_pct"]) == 4:
            lx_p, ly_p, lw_p, lh_p = vision_res["label_bbox_pct"]
            label_info["bbox"] = [
                int(orig_w * lx_p / 100.0),
                int(orig_h * ly_p / 100.0),
                int(orig_w * lw_p / 100.0),
                int(orig_h * lh_p / 100.0),
            ]
        target_counts = {"black": 0, "silver": 0}
        for vg in vision_res["groups"]:
            fk = (vg.get("finish_key") or "black").lower()
            qty = int(vg.get("count") or vg.get("quantity") or 0)
            if fk == "black":
                target_counts["black"] += qty
            else:
                target_counts["silver"] += qty

    seg_info = segment_and_classify_fasteners(
        img_bgr,
        label_bbox=label_info.get("bbox"),
        ruler_mm_per_px=ruler_mm_per_px,
        known_size=user_hints.get("size") or (vision_res and vision_res.get("detected_specs", {}).get("size")) or label_info.get("size"),
        known_length=user_hints.get("length") or (vision_res and vision_res.get("detected_specs", {}).get("length")) or label_info.get("length"),
        ruler_bbox=ruler_bbox_px,
        target_counts=target_counts,
    )
    black_pieces = seg_info["black_pieces"]
    silver_pieces = seg_info["silver_pieces"]

    if vision_res and isinstance(vision_res.get("groups"), list) and len(vision_res["groups"]) > 0:
        v_specs = vision_res.get("detected_specs") or {}
        resolved_size = user_hints.get("size") or v_specs.get("size") or label_info.get("size") or "M4"
        resolved_length = user_hints.get("length") or v_specs.get("length") or label_info.get("length") or "6 mm"
        base_specs = lookup_fastener_specs(resolved_size, head="shcs")
        resolved_pitch = user_hints.get("pitch") or v_specs.get("pitch") or base_specs.get("pitch") or "0.7 mm"

        v_groups: List[Dict[str, Any]] = []
        for idx, vg in enumerate(vision_res["groups"], start=1):
            g_size = vg.get("size") or resolved_size
            g_len = vg.get("length") or resolved_length
            g_head = (vg.get("head") or "shcs").lower()
            g_drive = (vg.get("drive") or "hex").lower()
            g_finish_key = (vg.get("finish_key") or "black").lower()
            g_finish = vg.get("finish") or ("Black Oxide Steel" if g_finish_key == "black" else "Stainless Steel (Silver)")
            g_comp = vg.get("comp_type") or ("nut" if g_head == "nut" else "washer" if g_head == "washer" else "insert" if g_head == "insert" else "bolt")
            g_qty = int(vg.get("count") or vg.get("quantity") or 1)
            grp_specs = lookup_fastener_specs(g_size, head=g_head, drive=g_drive)
            h_title = head_names.get(g_head, "Fastener")
            size_len_prefix = f"{g_size} × {g_len}".strip() if g_len and g_head not in ("nut", "washer") else g_size
            v_groups.append(
                {
                    "group_index": idx,
                    "finish_key": g_finish_key,
                    "finish": g_finish,
                    "count": g_qty,
                    "quantity": g_qty,
                    "size": g_size,
                    "length": g_len,
                    "pitch": grp_specs.get("pitch") or resolved_pitch,
                    "head": g_head,
                    "head_name": h_title,
                    "drive": g_drive,
                    "comp_type": g_comp,
                    "tool_key": grp_specs.get("tool_key", ""),
                    "tap_drill": grp_specs.get("tap_drill", ""),
                    "clearance_drill": grp_specs.get("clearance_drill", ""),
                    "name": f"{size_len_prefix} {h_title} ({g_finish})".replace("  ", " ").strip(),
                    "notes": vg.get("notes") or "",
                }
            )

        v_label_detected = bool(vision_res.get("label_detected") or label_info.get("detected"))
        ruler_calibrated = bool(ruler_mm_per_px and ruler_mm_per_px > 0)
        v_questions = vision_res.get("questions") or build_clarification_questions(
            label_detected=v_label_detected,
            size=resolved_size if v_label_detected else None,
            length=resolved_length if v_label_detected else None,
            groups=v_groups,
            ruler_calibrated=ruler_calibrated,
        )
        overlay_label_info = {
            "bbox": label_info.get("bbox"),
            "size": resolved_size,
            "length": resolved_length,
        }
        annotated_b64 = render_annotated_overlay(
            img_bgr=img_bgr,
            label_info=overlay_label_info,
            black_pieces=black_pieces,
            silver_pieces=silver_pieces,
        )
        cartridge_label = f"{resolved_size} × {resolved_length.replace(' mm', '')}" if resolved_size and resolved_length else ""
        return {
            "analysis_source": "agy_gemini_vision",
            "label_detected": v_label_detected,
            "label_ocr_text": vision_res.get("label_ocr_text") or label_info.get("raw_text", ""),
            "needs_clarification": not v_label_detected or len(v_questions) > 0,
            "ruler_calibrated": ruler_calibrated,
            "cartridge_label": cartridge_label,
            "detected_specs": {
                "size": resolved_size,
                "length": resolved_length,
                "pitch": resolved_pitch,
                "tap_drill": base_specs.get("tap_drill", ""),
                "clearance_drill": base_specs.get("clearance_drill", ""),
                "estimated_length_mm": seg_info.get("estimated_length_mm"),
                "estimated_size_guess": seg_info.get("estimated_size_guess"),
            },
            "total_pieces_detected": sum(g["count"] for g in v_groups),
            "groups": v_groups,
            "questions": v_questions,
            "annotated_image_base64": annotated_b64,
        }

    # Determine resolved size, length, and pitch (priority: user_hints -> label OCR -> ruler estimate -> educated guess)
    resolved_size = (
        user_hints.get("size")
        or label_info.get("size")
        or seg_info.get("estimated_size_guess")
        or "M4"
    )
    resolved_length = (
        user_hints.get("length")
        or label_info.get("length")
        or (f"{int(seg_info['estimated_length_mm'])} mm" if seg_info.get("estimated_length_mm") else None)
        or "6 mm"
    )

    base_specs = lookup_fastener_specs(resolved_size, head="shcs")
    resolved_pitch = user_hints.get("pitch") or label_info.get("pitch") or base_specs.get("pitch") or "0.7 mm"

    head_names = {
        "shcs": "Socket Head Cap Screw",
        "bhcs": "Button Head Cap Screw",
        "fhcs": "Flat Head Countersunk Screw",
        "hex": "Hex Head Bolt",
        "pan": "Pan Head Screw",
    }

    groups: List[Dict[str, Any]] = []

    if len(black_pieces) > 0:
        votes = [p["head_vote"] for p in black_pieces]
        maj_head = max(set(votes), key=votes.count) if votes else "shcs"
        grp_specs = lookup_fastener_specs(resolved_size, head=maj_head)
        h_title = head_names.get(maj_head, "Socket Head Cap Screw")
        groups.append(
            {
                "group_index": len(groups) + 1,
                "finish_key": "black",
                "finish": "Black Oxide Steel",
                "count": len(black_pieces),
                "quantity": len(black_pieces),
                "size": resolved_size,
                "length": resolved_length,
                "pitch": resolved_pitch,
                "head": maj_head,
                "head_name": h_title,
                "drive": "hex",
                "comp_type": "bolt",
                "tool_key": grp_specs.get("tool_key", ""),
                "tap_drill": grp_specs.get("tap_drill", ""),
                "clearance_drill": grp_specs.get("clearance_drill", ""),
                "name": f"{resolved_size} × {resolved_length} {h_title} (Black Oxide)",
                "notes": "Black oxide hardware stored separately inside cartridge bin.",
            }
        )

    if len(silver_pieces) > 0:
        votes = [p["head_vote"] for p in silver_pieces]
        maj_head = max(set(votes), key=votes.count) if votes else "bhcs"
        grp_specs = lookup_fastener_specs(resolved_size, head=maj_head)
        h_title = head_names.get(maj_head, "Button Head Cap Screw")
        groups.append(
            {
                "group_index": len(groups) + 1,
                "finish_key": "silver",
                "finish": "Stainless Steel (Silver)",
                "count": len(silver_pieces),
                "quantity": len(silver_pieces),
                "size": resolved_size,
                "length": resolved_length,
                "pitch": resolved_pitch,
                "head": maj_head,
                "head_name": h_title,
                "drive": "hex",
                "comp_type": "bolt",
                "tool_key": grp_specs.get("tool_key", ""),
                "tap_drill": grp_specs.get("tap_drill", ""),
                "clearance_drill": grp_specs.get("clearance_drill", ""),
                "name": f"{resolved_size} × {resolved_length} {h_title} (Stainless Steel)",
                "notes": "Silver / stainless hardware stored separately inside cartridge bin.",
            }
        )

    # Fallback if image had zero segmented blobs (e.g., blank photo)
    if not groups:
        grp_specs = lookup_fastener_specs(resolved_size, head="shcs")
        groups.append(
            {
                "group_index": 1,
                "finish_key": "black",
                "finish": "Black Oxide Steel",
                "count": 1,
                "quantity": 1,
                "size": resolved_size,
                "length": resolved_length,
                "pitch": resolved_pitch,
                "head": "shcs",
                "head_name": "Socket Head Cap Screw",
                "drive": "hex",
                "comp_type": "bolt",
                "tool_key": grp_specs.get("tool_key", ""),
                "tap_drill": grp_specs.get("tap_drill", ""),
                "clearance_drill": grp_specs.get("clearance_drill", ""),
                "name": f"{resolved_size} × {resolved_length} Socket Head Cap Screw",
                "notes": "",
            }
        )

    label_detected = bool(label_info.get("detected"))
    ruler_calibrated = bool(ruler_mm_per_px and ruler_mm_per_px > 0)
    questions = build_clarification_questions(
        label_detected=label_detected,
        size=label_info.get("size") or seg_info.get("estimated_size_guess"),
        length=label_info.get("length") or (f"{int(seg_info['estimated_length_mm'])} mm" if seg_info.get("estimated_length_mm") else None),
        groups=groups,
        ruler_calibrated=ruler_calibrated,
    )

    annotated_b64 = render_annotated_overlay(
        img_bgr=img_bgr,
        label_info=label_info,
        black_pieces=black_pieces,
        silver_pieces=silver_pieces,
    )

    cartridge_label = f"{resolved_size} × {resolved_length.replace(' mm', '')}" if resolved_size and resolved_length else ""

    return {
        "analysis_source": "opencv_fallback",
        "label_detected": label_detected,
        "label_ocr_text": label_info.get("raw_text", ""),
        "needs_clarification": not label_detected,
        "ruler_calibrated": ruler_calibrated,
        "cartridge_label": cartridge_label,
        "detected_specs": {
            "size": resolved_size,
            "length": resolved_length,
            "pitch": resolved_pitch,
            "tap_drill": base_specs.get("tap_drill", ""),
            "clearance_drill": base_specs.get("clearance_drill", ""),
            "estimated_length_mm": seg_info.get("estimated_length_mm"),
            "estimated_size_guess": seg_info.get("estimated_size_guess"),
        },
        "total_pieces_detected": sum(g["count"] for g in groups),
        "groups": groups,
        "questions": questions,
        "annotated_image_base64": annotated_b64,
    }
