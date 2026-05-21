#!/usr/bin/env python3
"""
⚡ AI Electric Eye — AI的电眼神通
A pixel-level visual perception toolkit for AI agents.

AI models can "see" images through vision APIs, but they often fail at:
- Distinguishing similar colors (orange cloud vs gray cloud in Cloudflare)
- Measuring distances between elements
- Detecting element boundaries
- Reading color values precisely

This tool gives AI what glasses give to humans: precise, deterministic perception.

Usage:
  python3 color_picker.py <image>                          # Analyze dominant colors
  python3 color_picker.py <image> x1 y1 [x2 y2 ...]       # Pick pixel colors
  python3 color_picker.py <image> --cloudflare              # Detect Cloudflare DNS cloud icons
  python3 color_picker.py <image> --dist x1 y1 x2 y2       # Measure distance between two points
  python3 color_picker.py <image> --element x y [tolerance] # Auto-detect element boundaries
  python3 color_picker.py <image> --hruler y                # Horizontal scan line
  python3 color_picker.py <image> --vruler x                # Vertical scan line

Requirements: Python 3.6+, Pillow (pip install Pillow)
License: MIT
"""

import sys
import math
from PIL import Image
from collections import Counter, defaultdict


def rgb_to_name(r, g, b):
    """Convert RGB values to approximate color name."""
    colors = {
        'Red': (255, 0, 0), 'Orange': (255, 165, 0), 'Yellow': (255, 255, 0),
        'Green': (0, 128, 0), 'Cyan': (0, 255, 255), 'Blue': (0, 0, 255),
        'Purple': (128, 0, 128), 'White': (255, 255, 255), 'Black': (0, 0, 0),
        'Gray': (128, 128, 128), 'Dark Gray': (64, 64, 64), 'Light Gray': (192, 192, 192),
        'Deep Orange': (200, 100, 0), 'Light Orange': (255, 200, 128),
    }
    min_dist = float('inf')
    name = 'Unknown'
    for n, (cr, cg, cb) in colors.items():
        dist = ((r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2) ** 0.5
        if dist < min_dist:
            min_dist = dist
            name = n
    return name


def analyze_image(path, sample_step=10):
    """Sample and analyze dominant colors in an image."""
    img = Image.open(path).convert('RGB')
    w, h = img.size
    counter = Counter()
    total = 0
    for x in range(0, w, sample_step):
        for y in range(0, h, sample_step):
            r, g, b = img.getpixel((x, y))
            name = rgb_to_name(r, g, b)
            counter[name] += 1
            total += 1
    print(f"Image size: {w}x{h} | Samples: {total} pixels | Step: {sample_step}")
    print("Dominant colors:")
    for name, count in counter.most_common(10):
        pct = count / total * 100
        bar = '█' * int(pct / 2)
        print(f"  {name:>12}: {pct:5.1f}% {bar}")


def pick_pixels(path, coords):
    """Pick exact color values at specified pixel coordinates."""
    img = Image.open(path).convert('RGB')
    w, h = img.size
    for i in range(0, len(coords), 2):
        x, y = coords[i], coords[i + 1]
        if x >= w or y >= h:
            print(f"Coordinate ({x},{y}) out of image bounds ({w}x{h})")
            continue
        r, g, b = img.getpixel((x, y))
        name = rgb_to_name(r, g, b)
        hex_c = f'#{r:02X}{g:02X}{b:02X}'
        print(f"Pixel ({x},{y}): RGB({r},{g},{b}) HEX={hex_c} → {name}")


def measure_distance(path, x1, y1, x2, y2):
    """Measure pixel distance between two points."""
    img = Image.open(path).convert('RGB')
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    dist = math.sqrt(dx ** 2 + dy ** 2)
    angle = math.degrees(math.atan2(dy, dx))
    print(f"📏 Distance: ({x1},{y1}) → ({x2},{y2})")
    print(f"   Horizontal: {dx}px | Vertical: {dy}px | Direct: {dist:.1f}px | Angle: {angle:.1f}°")
    for label, x, y in [("Start", x1, y1), ("End", x2, y2)]:
        if 0 <= x < img.size[0] and 0 <= y < img.size[1]:
            r, g, b = img.getpixel((x, y))
            hex_c = f'#{r:02X}{g:02X}{b:02X}'
            print(f"   {label}({x},{y}): RGB({r},{g},{b}) {hex_c} → {rgb_to_name(r, g, b)}")


def measure_element(path, x, y, tolerance=30):
    """Auto-detect element boundaries based on color similarity."""
    img = Image.open(path).convert('RGB')
    w, h = img.size
    r0, g0, b0 = img.getpixel((x, y))

    def find_edge(start, end, step, fixed, axis):
        for pos in range(start, end, step):
            if axis == 'x':
                px, py = pos, fixed
            else:
                px, py = fixed, pos
            if 0 <= px < w and 0 <= py < h:
                r, g, b = img.getpixel((px, py))
                if abs(r - r0) > tolerance or abs(g - g0) > tolerance or abs(b - b0) > tolerance:
                    return pos
        return end

    left = find_edge(x, -1, -1, y, 'x')
    right = find_edge(x, w, 1, y, 'x')
    top = find_edge(y, -1, -1, x, 'y')
    bottom = find_edge(y, h, 1, x, 'y')

    width = right - left
    height = bottom - top

    print(f"📏 Element at ({x},{y}) RGB({r0},{g0},{b0}) → {rgb_to_name(r0, g0, b0)}")
    print(f"   Bounds: L={left} R={right} T={top} B={bottom}")
    print(f"   Size: {width}×{height}px | Tolerance: ±{tolerance}")
    for label, cx, cy in [("TL", left + 1, top + 1), ("TR", right - 1, top + 1),
                           ("BL", left + 1, bottom - 1), ("BR", right - 1, bottom - 1)]:
        if 0 <= cx < w and 0 <= cy < h:
            r, g, b = img.getpixel((cx, cy))
            print(f"   {label}({cx},{cy}): RGB({r},{g},{b}) → {rgb_to_name(r, g, b)}")


def scan_ruler(path, y=None, x=None):
    """Scan horizontal/vertical line showing color segments and widths."""
    img = Image.open(path).convert('RGB')
    w, h = img.size

    if y is not None:
        print(f"📐 Horizontal scan y={y} | Width={w}px")
        segments = []
        prev_color = None
        start_x = 0
        for sx in range(0, w, 3):
            r, g, b = img.getpixel((sx, y))
            color = rgb_to_name(r, g, b)
            if color != prev_color and prev_color is not None:
                segments.append((start_x, sx, prev_color))
                start_x = sx
            prev_color = color
        if prev_color:
            segments.append((start_x, w, prev_color))
        for sx, ex, color in segments[:25]:
            width = ex - sx
            print(f"  x={sx:>4}-{ex:>4} ({width:>4}px): {color}")
        if len(segments) > 25:
            print(f"  ... {len(segments)} segments total")

    if x is not None:
        print(f"📐 Vertical scan x={x} | Height={h}px")
        segments = []
        prev_color = None
        start_y = 0
        for sy in range(0, h, 3):
            r, g, b = img.getpixel((x, sy))
            color = rgb_to_name(r, g, b)
            if color != prev_color and prev_color is not None:
                segments.append((start_y, sy, prev_color))
                start_y = sy
            prev_color = color
        if prev_color:
            segments.append((start_y, h, prev_color))
        for sy, ey, color in segments[:25]:
            height = ey - sy
            print(f"  y={sy:>4}-{ey:>4} ({height:>4}px): {color}")
        if len(segments) > 25:
            print(f"  ... {len(segments)} segments total")


def detect_cloudflare_clouds(path):
    """Detect orange/gray cloud icons in Cloudflare DNS panel screenshots."""
    img = Image.open(path).convert('RGB')
    w, h = img.size
    orange_pixels = defaultdict(list)
    for y in range(h):
        for x in range(max(0, w // 3), w):
            r, g, b = img.getpixel((x, y))
            if r > 200 and g > 100 and b < 160 and (r - b) > 80:
                row_key = y // 40
                orange_pixels[row_key].append((x, y, r, g, b))
    gray_pixels = defaultdict(list)
    for y in range(h):
        for x in range(max(0, w // 3), w):
            r, g, b = img.getpixel((x, y))
            if abs(r - g) < 20 and abs(r - b) < 20 and abs(g - b) < 20:
                if 160 < r < 210:
                    row_key = y // 40
                    gray_pixels[row_key].append((x, y, r, g, b))
    all_rows = set(list(orange_pixels.keys()) + list(gray_pixels.keys()))
    print(f"Image size: {w}x{h}")
    print("=== Cloudflare DNS Cloud Detection ===")
    for row_key in sorted(all_rows):
        orange_count = len(orange_pixels.get(row_key, []))
        gray_count = len(gray_pixels.get(row_key, []))
        y_min = min(p[1] for p in (orange_pixels.get(row_key, []) + gray_pixels.get(row_key, [])))
        if orange_count > gray_count * 2 and orange_count > 20:
            cloud = "🟠 Orange Cloud (CDN Proxy)"
        elif gray_count > orange_count * 2 and gray_count > 20:
            cloud = "⚪ Gray Cloud (DNS Only)"
        elif orange_count > 20:
            cloud = f"🟠 Orange-ish (orange:{orange_count} gray:{gray_count})"
        elif gray_count > 20:
            cloud = f"⚪ Gray-ish (orange:{orange_count} gray:{gray_count})"
        else:
            continue
        print(f"  y≈{y_min:>3}: {cloud}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    path = sys.argv[1]
    args = sys.argv[2:]

    if '--cloudflare' in args:
        detect_cloudflare_clouds(path)
    elif '--dist' in args:
        idx = args.index('--dist')
        x1, y1, x2, y2 = int(args[idx + 1]), int(args[idx + 2]), int(args[idx + 3]), int(args[idx + 4])
        measure_distance(path, x1, y1, x2, y2)
    elif '--element' in args:
        idx = args.index('--element')
        x, y = int(args[idx + 1]), int(args[idx + 2])
        tol = int(args[idx + 3]) if idx + 3 < len(args) else 30
        measure_element(path, x, y, tol)
    elif '--hruler' in args:
        idx = args.index('--hruler')
        y = int(args[idx + 1])
        scan_ruler(path, y=y)
    elif '--vruler' in args:
        idx = args.index('--vruler')
        x = int(args[idx + 1])
        scan_ruler(path, x=x)
    else:
        coords = [int(x) for x in args]
        if len(coords) >= 2 and len(coords) % 2 == 0:
            pick_pixels(path, coords)
        else:
            analyze_image(path)
