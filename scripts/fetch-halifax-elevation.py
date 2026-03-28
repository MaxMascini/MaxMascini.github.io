#!/usr/bin/env python3
"""
Fetch NRCan HRDEM (LiDAR 1m) elevation data for Halifax via STAC + Cloud
Optimized GeoTIFF. Only the Halifax window is downloaded from the remote COG —
no multi-hundred-MB tile downloads needed.

Dependencies: pip install rasterio
Run:          python3 scripts/fetch-halifax-elevation.py
Output:       public/data/halifax-elevation.json
"""

import json
import os
import urllib.request

import numpy as np

try:
    import rasterio
    from rasterio.crs import CRS
    from rasterio.warp import transform_bounds
    from rasterio.windows import from_bounds as window_from_bounds
    from rasterio.enums import Resampling
except ImportError:
    raise SystemExit(
        "\n  Missing dependency: pip install rasterio\n"
    )

# ── Output grid ─────────────────────────────────────────────────────────────
GRID_W = 140
GRID_H = 88

# ── View bounds (WGS84) ──────────────────────────────────────────────────────
BOUNDS = {
    "latMin": 44.50,
    "latMax": 44.76,
    "lonMin": -63.76,
    "lonMax": -63.33,
}

WGS84 = CRS.from_epsg(4326)

# ── Step 1: Find the DTM COG URL via STAC ───────────────────────────────────
print("Searching NRCan STAC for HRDEM 1m tile covering Halifax…")

stac_url = (
    "https://datacube.services.geo.ca/stac/api/search"
    "?collections=hrdem-mosaic-1m"
    f"&bbox={BOUNDS['lonMin']},{BOUNDS['latMin']},{BOUNDS['lonMax']},{BOUNDS['latMax']}"
    "&limit=5"
)

with urllib.request.urlopen(stac_url, timeout=30) as resp:
    stac = json.loads(resp.read())

features = stac.get("features", [])
if not features:
    raise SystemExit("No HRDEM items found for Halifax bounds — check STAC endpoint.")

# Collect unique DTM COG URLs (there may be multiple tiles)
cog_urls = []
for f in features:
    href = f.get("assets", {}).get("dtm", {}).get("href")
    if href and href not in cog_urls:
        cog_urls.append(href)

print(f"  Found {len(cog_urls)} tile(s): {[u.split('/')[-1] for u in cog_urls]}")

# ── Step 2: Windowed read from each COG, mosaic in memory ───────────────────
print("Reading Halifax window from remote COG(s) (only this area is downloaded)…")

# Accumulate weighted sum for averaging where tiles overlap
acc   = np.zeros((GRID_H, GRID_W), dtype=np.float64)
count = np.zeros((GRID_H, GRID_W), dtype=np.int32)

for cog_url in cog_urls:
    print(f"  Opening: {cog_url.split('/')[-1]}")
    with rasterio.open(cog_url) as src:
        file_crs = src.crs

        # Transform our WGS84 bounds into the file's native CRS
        west, south, east, north = transform_bounds(
            WGS84, file_crs,
            BOUNDS["lonMin"], BOUNDS["latMin"],
            BOUNDS["lonMax"], BOUNDS["latMax"],
        )

        # Build a window for this bounding box
        window = window_from_bounds(west, south, east, north, transform=src.transform)

        # Clamp window to the file extent (tile may not cover full bbox)
        window = window.intersection(
            rasterio.windows.Window(0, 0, src.width, src.height)
        )
        if window.width <= 0 or window.height <= 0:
            print("    (no overlap — skipping)")
            continue

        # Read at target resolution using bilinear resampling
        tile_data = src.read(
            1,
            window=window,
            out_shape=(GRID_H, GRID_W),
            resampling=Resampling.bilinear,
        ).astype(np.float64)

        nodata = src.nodata
        print(f"    NoData value: {nodata}")

    # Mask NoData
    if nodata is not None:
        valid = tile_data != nodata
    else:
        valid = np.isfinite(tile_data)

    acc[valid]   += tile_data[valid]
    count[valid] += 1

if count.max() == 0:
    raise SystemExit("No data read — tiles may not cover Halifax bounds.")

# Average where tiles overlap; 0 where no coverage (treated as ocean/NoData)
grid = np.divide(acc, count, out=np.zeros_like(acc), where=count > 0)

print(f"  Raw elevation range: {grid[count>0].min():.1f}m – {grid[count>0].max():.1f}m")
print(f"  Coverage: {(count>0).sum()} / {count.size} cells ({(count>0).mean()*100:.0f}%)")

# ── Step 3: Normalise ────────────────────────────────────────────────────────
# Ocean/water cells (no data, elevation ≤ 0) → -1.0
# Land cells (elevation > 0) → normalised to [0, 1]
# Large gap between ocean (-1.0) and land ([0,1]) means the renderer can draw
# contours only over land and leave ocean completely blank.
land_mask = (count > 0) & (grid > 0)

if not land_mask.any():
    raise SystemExit("No land cells found — check bounds or data coverage.")

vmin = grid[land_mask].min()
vmax = grid[land_mask].max()
norm = np.where(land_mask, (grid - vmin) / (vmax - vmin), -1.0)

print(f"  Land cells: {land_mask.sum()} / {land_mask.size} ({land_mask.mean()*100:.0f}%)")
print(f"  Ocean cells → -1.0")

flat = [round(float(v), 2) for v in norm.flatten()]

# ── Step 4: Write JSON ───────────────────────────────────────────────────────
out = {
    "grid_w": GRID_W,
    "grid_h": GRID_H,
    "bounds": BOUNDS,
    "elevation": flat,
}

out_path = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "public", "data", "halifax-elevation.json")
)
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w") as f:
    json.dump(out, f, separators=(",", ":"))

print(f"\n✓ Written to {out_path} ({os.path.getsize(out_path)/1024:.1f} KB)")

# ── ASCII preview ────────────────────────────────────────────────────────────
print("\nASCII preview (every other column):")
for r in range(GRID_H):
    row = flat[r * GRID_W:(r + 1) * GRID_W]
    print("".join(
        "~" if v <= -0.9 else " " if v < -0.5 else "." if v < 0 else ":" if v < 0.4 else "#"
        for v in row[::2]
    ))
