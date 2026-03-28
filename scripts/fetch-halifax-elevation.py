#!/usr/bin/env python3
"""
Fetch NRCan HRDEM (LiDAR 1m) elevation data for Halifax.

Priority:
  1. Local GeoTIFF at scripts/halifax-hrdem.tif  (drop file here to use it)
  2. Remote COG via NRCan STAC API               (fallback, no download needed)

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

LOCAL_TIFF = os.path.join(os.path.dirname(__file__), "halifax-hrdem.tif")

# ── Accumulator (used by both paths) ─────────────────────────────────────────
acc   = np.zeros((GRID_H, GRID_W), dtype=np.float64)
count = np.zeros((GRID_H, GRID_W), dtype=np.int32)


def read_tiff(path_or_url: str) -> None:
    """Windowed-read one GeoTIFF (local or remote COG) into acc/count."""
    print(f"  Opening: {os.path.basename(path_or_url)}")
    with rasterio.open(path_or_url) as src:
        file_crs = src.crs

        if file_crs == WGS84 or file_crs.to_epsg() == 4326:
            west, south, east, north = (
                BOUNDS["lonMin"], BOUNDS["latMin"],
                BOUNDS["lonMax"], BOUNDS["latMax"],
            )
        else:
            west, south, east, north = transform_bounds(
                WGS84, file_crs,
                BOUNDS["lonMin"], BOUNDS["latMin"],
                BOUNDS["lonMax"], BOUNDS["latMax"],
            )

        window = window_from_bounds(west, south, east, north, transform=src.transform)
        window = window.intersection(
            rasterio.windows.Window(0, 0, src.width, src.height)
        )
        if window.width <= 0 or window.height <= 0:
            print("    (no overlap — skipping)")
            return

        tile_data = src.read(
            1,
            window=window,
            out_shape=(GRID_H, GRID_W),
            resampling=Resampling.bilinear,
        ).astype(np.float64)

        nodata = src.nodata
        print(f"    NoData value: {nodata}  |  CRS: {file_crs.to_epsg()}")

    # For local file with no NoData tag, zeros are ocean (no LiDAR return)
    if nodata is not None:
        valid = tile_data != nodata
    else:
        valid = (tile_data != 0) & np.isfinite(tile_data)

    acc[valid]   += tile_data[valid]
    count[valid] += 1


# ── Step 1 & 2: Load data ─────────────────────────────────────────────────────
if os.path.exists(LOCAL_TIFF):
    print(f"Using local GeoTIFF: {LOCAL_TIFF}")
    read_tiff(LOCAL_TIFF)
else:
    print("Local file not found — querying NRCan STAC for remote COG…")
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

    cog_urls = []
    for f in features:
        href = f.get("assets", {}).get("dtm", {}).get("href")
        if href and href not in cog_urls:
            cog_urls.append(href)

    print(f"  Found {len(cog_urls)} tile(s): {[u.split('/')[-1] for u in cog_urls]}")
    for cog_url in cog_urls:
        read_tiff(cog_url)

if count.max() == 0:
    raise SystemExit("No data read — file may not cover Halifax bounds.")

# Average where tiles overlap; 0 where no coverage (ocean)
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
