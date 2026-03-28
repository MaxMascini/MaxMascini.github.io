#!/usr/bin/env python3
"""
Download SRTM elevation data for the Halifax peninsula from the AWS terrain
tiles Skadi endpoint (public, no auth) and save as static JSON.

Run once: python3 scripts/fetch-halifax-elevation.py
Output:   public/data/halifax-elevation.json

Source: https://s3.amazonaws.com/elevation-tiles-prod/skadi/N44/N44W064.hgt.gz
  - Raw SRTM 1-arc-second (30m), 1201x1201 int16 big-endian
  - Ocean/harbour/NoData = -32768 → mapped to -1.0 (sparse contours)
  - Land values normalised so peninsula topography spans [-1, 1]
"""

import gzip
import io
import json
import os
import urllib.request

import numpy as np

# ── Grid config ───────────────────────────────────────────
GRID_W = 140
GRID_H = 88

# Bounds: peninsula sits upper-left with enough ocean context to be readable.
BOUNDS = {
    "latMin": 44.50,
    "latMax": 44.76,
    "lonMin": -63.76,
    "lonMax": -63.33,
}

# ── Download SRTM tile ─────────────────────────────────────
# Tile N44W064 covers 44–45°N, 63–64°W (Halifax sits inside this tile)
URL = "https://s3.amazonaws.com/elevation-tiles-prod/skadi/N44/N44W064.hgt.gz"

print(f"Downloading SRTM tile from AWS…")
print(f"  {URL}")

with urllib.request.urlopen(URL, timeout=60) as resp:
    compressed = resp.read()

size_kb = len(compressed) / 1024
print(f"  Downloaded {size_kb:.0f} KB")

# ── Decompress + parse ─────────────────────────────────────
raw = gzip.decompress(compressed)
# 1201×1201 int16 big-endian = 2,884,802 bytes
arr = np.frombuffer(raw, dtype=">i2").reshape(3601, 3601).astype(float)

print(f"  Tile shape: {arr.shape}")

# ── Mask ocean/NoData ──────────────────────────────────────
# SRTM void = -32768 (ocean, lakes, data gaps)
arr[arr == -32768] = 0

# ── Crop to Halifax bounds ─────────────────────────────────
# Tile covers exactly 44.0–45.0°N (row 0 = 45°N, row 1200 = 44°N)
#                      -64.0 – -63.0°W (col 0 = -64°W, col 1200 = -63°W)
def lat_to_row(lat):
    return round((45.0 - lat) * 3600)   # SRTM1: 3600 samples per degree

def lon_to_col(lon):
    return round((lon - (-64.0)) * 3600)

row_min = lat_to_row(BOUNDS["latMax"])   # north edge → smaller row index
row_max = lat_to_row(BOUNDS["latMin"])   # south edge → larger row index
col_min = lon_to_col(BOUNDS["lonMin"])
col_max = lon_to_col(BOUNDS["lonMax"])

cropped = arr[row_min:row_max + 1, col_min:col_max + 1]
print(f"  Cropped shape: {cropped.shape} (rows {row_min}–{row_max}, cols {col_min}–{col_max})")
print(f"  Elevation range in crop: {int(cropped.min())}m – {int(cropped.max())}m")

# ── Downsample to output grid ──────────────────────────────
try:
    from scipy.ndimage import zoom as scipy_zoom
    scale_r = GRID_H / cropped.shape[0]
    scale_c = GRID_W / cropped.shape[1]
    grid = scipy_zoom(cropped, (scale_r, scale_c), order=1)
    print(f"  Downsampled to {grid.shape} using scipy bilinear zoom")
except ImportError:
    # Fallback: simple nearest-neighbour slice (numpy only)
    row_idx = [round(i * (cropped.shape[0] - 1) / (GRID_H - 1)) for i in range(GRID_H)]
    col_idx = [round(i * (cropped.shape[1] - 1) / (GRID_W - 1)) for i in range(GRID_W)]
    grid = cropped[np.ix_(row_idx, col_idx)]
    print(f"  Downsampled to {grid.shape} using index slicing (scipy not available)")

# ── Normalise ──────────────────────────────────────────────
# Ocean/water cells (raw value <= 0) → -1.0
# Land cells (raw value > 0) → normalised to [0, 1]
# The large gap between ocean (-1.0) and land ([0, 1]) means the renderer
# can draw contours only over land (levels 0.02–0.98) and the ocean area
# stays completely blank — no contour lines along the coastline.
land_mask = grid > 0
if land_mask.any():
    vmin = grid[land_mask].min()
    vmax = grid[land_mask].max()
    norm_grid = np.where(land_mask, (grid - vmin) / (vmax - vmin), -1.0)
else:
    norm_grid = np.full_like(grid, -1.0)

print(f"  Land cells: {land_mask.sum()} / {land_mask.size} ({land_mask.mean()*100:.0f}%)")
print(f"  Ocean cells set to -1.0 (below all contour levels)")

# Flatten to row-major list, round to 2 dp
flat = [round(float(v), 2) for v in norm_grid.flatten()]

# ── Write JSON ─────────────────────────────────────────────
out = {
    "grid_w": GRID_W,
    "grid_h": GRID_H,
    "bounds": BOUNDS,
    "elevation": flat,
}

out_path = os.path.join(os.path.dirname(__file__), "..", "public", "data", "halifax-elevation.json")
out_path = os.path.normpath(out_path)

os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w") as f:
    json.dump(out, f, separators=(",", ":"))

size_out_kb = os.path.getsize(out_path) / 1024
print(f"\n✓ Written to {out_path} ({size_out_kb:.1f} KB)")

# ── ASCII preview ──────────────────────────────────────────
print("\nASCII preview (every other col):")
for r in range(GRID_H):
    row = flat[r * GRID_W:(r + 1) * GRID_W]
    print("".join(
        "~" if v <= -0.9 else " " if v < -0.5 else "." if v < 0 else ":" if v < 0.4 else "#"
        for v in row[::2]
    ))
