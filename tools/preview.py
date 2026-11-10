#!/usr/bin/env python3
"""Lays every built texture out on one sheet, 8x, with names, to look the art over.

Usage: preview.py <build dir> <out.png>
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

SCALE, CELL, COLS = 6, 112, 12
root, out = Path(sys.argv[1]), Path(sys.argv[2])
files = sorted(root.glob("*/assets/*/textures/*/*.png"), key=lambda p: (p.parts[-4], p.parent.name, p.stem))
rows = (len(files) + COLS - 1) // COLS
sheet = Image.new("RGBA", (COLS * CELL, rows * CELL), (40, 42, 48, 255))
draw = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    x, y = i % COLS * CELL, i // COLS * CELL
    img = Image.open(f).convert("RGBA").resize((16 * SCALE, 16 * SCALE), Image.NEAREST)
    sheet.alpha_composite(img, (x + (CELL - 16 * SCALE) // 2, y + 2))
    draw.text((x + 3, y + 16 * SCALE + 2), f.stem[:18], fill=(220, 220, 220, 255))
sheet.save(out)
print(out, len(files), "textures")
