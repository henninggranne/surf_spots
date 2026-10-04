"""Rank Sentinel-2 frames over the Jomfruland SE shore by similarity to known good days.

Frame = the user's Copernicus Browser view (~4.7 x 3.5 km, zoom ~14).
For every pass in the chosen years (no wave/wind filter) a small true-colour + NIR crop is
downloaded (cached in ./cache_frame), features are computed on the exposed SE side of the
island, and frames are ranked by distance to the nearest truth frame.

  python match_truths.py --year 2025
  python match_truths.py --year 2025 --truth 2018-01-28 2026-04-04 --top 24

Output: frames/<date>.jpg (true colour), matches.csv.
"""
import argparse
import io
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import tifffile
from PIL import Image
from scipy import ndimage as ndi

from cdse import Auth, PROCESS, STAC, CLOUD_CLASSES

# lon_min, lat_min, lon_max, lat_max
FRAME = (9.540, 58.830, 9.622, 58.862)
W, H = 472, 356  # ~10 m pixels
# Rough line along the island (SW tip -> NE exit); water south-east of it is the exposed side
ISLAND_LINE = ((9.545, 58.833), (9.600, 58.862))

CACHE = Path("cache_frame")
FRAMES = Path("frames")

EVAL = {
    "l2a": """//VERSION=3
function setup(){return{input:[{bands:["B02","B03","B04","B08","SCL","dataMask"]}],
output:{bands:6,sampleType:"FLOAT32"}}}
function evaluatePixel(s){return[s.B02,s.B03,s.B04,s.B08,s.SCL,s.dataMask]}""",
    "l1c": """//VERSION=3
function setup(){return{input:[{bands:["B02","B03","B04","B08","dataMask"]}],
output:{bands:6,sampleType:"FLOAT32"}}}
function evaluatePixel(s){return[s.B02,s.B03,s.B04,s.B08,0,s.dataMask]}""",
}


def list_dates(year, max_cloud):
    body = {"collections": ["sentinel-2-l2a"], "bbox": list(FRAME), "limit": 200,
            "datetime": f"{year}-01-01T00:00:00Z/{year}-12-31T23:59:59Z"}
    feats = []
    url = STAC
    while url:
        r = requests.post(url, json=body, timeout=120)
        r.raise_for_status()
        j = r.json()
        feats += j["features"]
        nxt = [l for l in j.get("links", []) if l.get("rel") == "next"]
        url, body = (nxt[0]["href"], nxt[0].get("body", body)) if nxt else (None, None)
    dates = {f["properties"]["datetime"][:10] for f in feats
             if (f["properties"].get("eo:cloud_cover") or 0) < max_cloud}
    return sorted(dates)


def download(auth, date, level):
    payload = {
        "input": {
            "bounds": {"bbox": list(FRAME),
                       "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}},
            "data": [{"type": f"sentinel-2-{level}",
                      "dataFilter": {"timeRange": {"from": f"{date}T00:00:00Z",
                                                   "to": f"{date}T23:59:59Z"},
                                     "mosaickingOrder": "leastCC"}}],
        },
        "output": {"width": W, "height": H,
                   "responses": [{"identifier": "default", "format": {"type": "image/tiff"}}]},
        "evalscript": EVAL[level],
    }
    for attempt in range(4):
        r = requests.post(PROCESS, json=payload, headers=auth.header(), timeout=300)
        if r.status_code == 429:
            time.sleep(10 * (attempt + 1))
            continue
        r.raise_for_status()
        a = tifffile.imread(io.BytesIO(r.content))
        if a[..., 5].mean() < 0.5:  # mostly no data
            return False
        np.savez_compressed(CACHE / f"{date}.npz", rgbn=a[..., :4].astype(np.float16),
                            scl=a[..., 4].astype(np.uint8), mask=a[..., 5].astype(np.uint8),
                            level=level)
        return True
    return False


def load(date):
    z = np.load(CACHE / f"{date}.npz")
    return z["rgbn"].astype(np.float32), z["scl"], z["mask"]


def save_jpeg(date, rgbn):
    rgb = np.clip(rgbn[..., [2, 1, 0]] * 2.5, 0, 1) ** (1 / 1.3)  # Copernicus-like true colour
    Image.fromarray((rgb * 255).astype(np.uint8)).save(FRAMES / f"{date}.jpg", quality=88)


def exposed_side():
    (lo0, la0), (lo1, la1) = ISLAND_LINE
    lon = np.linspace(FRAME[0], FRAME[2], W)[None, :]
    lat = np.linspace(FRAME[3], FRAME[1], H)[:, None]
    # sign of cross product: negative = right of the SW->NE line = south-east
    return ((lo1 - lo0) * (lat - la0) - (la1 - la0) * (lon - lo0)) < 0


def build_land(dates):
    stack = []
    for d in dates:
        rgbn, scl, mask = load(d)
        if mask.mean() > 0.95 and np.isin(scl, CLOUD_CLASSES).mean() < 0.02:
            stack.append(rgbn[..., 3])
    land = np.median(np.stack(stack), axis=0) > 0.08
    land = ndi.binary_opening(land, iterations=1)
    return ndi.binary_dilation(land, iterations=1)


def features(date, land, dist, se):
    rgbn, scl, mask = load(date)
    nir, red = rgbn[..., 3], rgbn[..., 2]
    # SCL flags white water as cloud/snow. Drop cloud blobs that stay within 300 m of shore.
    lab, n = ndi.label(np.isin(scl, CLOUD_CLASSES) & ~land)
    keep = np.zeros(n + 1, bool)
    if n:
        keep[1:] = ndi.maximum(dist, lab, index=np.arange(1, n + 1)) > 30
    cloud = ndi.binary_dilation(keep[lab], iterations=5)
    zone = se & ~land & (dist <= 150)
    valid = zone & (mask == 1) & ~cloud
    clear = valid.sum() / max(zone.sum(), 1)
    open_w = valid & (dist >= 40)
    if clear < 0.5 or open_w.sum() < 2000:
        return dict(date=date, clear=clear)

    base = np.median(nir[open_w])
    # Surf profile: NIR excess vs open water in 50 m bins out to 400 m from shore
    prof = []
    for a in range(0, 40, 5):
        m = valid & (dist > a) & (dist <= a + 5)
        prof.append(np.median(nir[m]) - base if m.sum() > 50 else 0.0)
    # Foam from 20 m offshore outward: the first 2 pixels mix beach and water, and snow on
    # the beach lights them up on flat days. Real white water reaches further out.
    fz = valid & (dist > 2) & (dist <= 25)
    foam = ((nir > base + 0.04) & fz).sum() / max(fz.sum(), 1)

    # Swell texture: band-pass red on open water, power in 40-200 m wavelengths
    x = np.where(open_w, red, np.median(red[open_w]))
    band = ndi.gaussian_filter(x, 1.0) - ndi.gaussian_filter(x, 8.0)
    texture = band[open_w].std() / max(np.median(red[open_w]), 0.02)
    haze = np.median(rgbn[..., 0][open_w])  # blue over open water: haze/thin cloud indicator
    # Cloud the SCL missed: bright patches far offshore (white water only exists at the shore)
    blue = rgbn[..., 0]
    far = valid & (dist >= 60)
    cloudy = (blue[far] > np.median(blue[far]) + 0.03).mean() if far.sum() > 1000 else 1.0
    # Whitecaps: small isolated bright specks far offshore = strong wind, choppy sea.
    # Cloud comes as big blobs, so only components of <= 4 pixels count.
    specks, ns = ndi.label(far & (nir > base + 0.03))
    sizes = np.bincount(specks.ravel())[1:] if ns else np.array([])
    whitecaps = sizes[sizes <= 4].sum() / max(far.sum(), 1)
    out = dict(date=date, clear=clear, foam=foam, texture=texture, haze=haze, base=base,
               cloudy=cloudy, whitecaps=whitecaps)
    out.update({f"p{i}": v for i, v in enumerate(prof)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, nargs="+", default=[2025])
    ap.add_argument("--truth", nargs="+", default=["2018-01-28", "2026-04-04"])
    ap.add_argument("--max-cloud", type=float, default=80)
    ap.add_argument("--top", type=int, default=24)
    ap.add_argument("--max-cloudy", type=float, default=0.01,
                    help="max fraction of bright offshore pixels (missed cloud)")
    ap.add_argument("--out", default="matches.csv")
    ap.add_argument("--recipe", help="recipe_days.csv: only download/score dates listed there")
    args = ap.parse_args()
    CACHE.mkdir(exist_ok=True)
    FRAMES.mkdir(exist_ok=True)
    auth = Auth()

    dates = []
    for y in args.year:
        ds = list_dates(y, args.max_cloud)
        print(f"{y}: {len(ds)} pass dates")
        dates += ds
    if args.recipe:
        # Only pass dates that match the wave recipe (see recipe_days.py)
        keep = set(pd.read_csv(args.recipe).date)
        dates = [d for d in dates if d in keep]
        print(f"{len(dates)} of them are recipe days")
    ok = []
    for i, d in enumerate(sorted(set(dates) | set(args.truth)), 1):
        if not (CACHE / f"{d}.npz").exists():
            got = False
            for level in ("l2a", "l1c"):
                try:
                    got = download(auth, d, level)
                except requests.HTTPError as e:
                    print(f"  {d} {level}: {e}")
                if got:
                    print(f"[{i}] {d} {level}")
                    break
            if not got:
                print(f"[{i}] {d} no data")
                continue
        ok.append(d)
        save_jpeg(d, load(d)[0])

    land = build_land(ok)
    dist = ndi.distance_transform_edt(~land)
    se = exposed_side()
    df = pd.DataFrame([features(d, land, dist, se) for d in ok])
    df["truth"] = df.date.isin(args.truth)

    # Usable = enough clear exposed water and no missed cloud offshore (truths always kept)
    usable = df.dropna(subset=["foam"])
    usable = usable[(usable.cloudy < args.max_cloudy) | usable.truth].copy()
    # Surf signal on the same scale as the truths: foam at the shore, near-shore brightening,
    # swell texture (robust z-scores, capped so one outlier feature can't dominate)
    usable["nearshore"] = usable[["p0", "p1", "p2"]].mean(axis=1)
    usable["score"] = sum(robust_z(usable[c]).clip(-3, 10) for c in ("foam", "nearshore", "texture"))
    usable = usable.sort_values("score", ascending=False).reset_index(drop=True)
    usable["rank"] = usable.index + 1

    rest = df[~df.date.isin(usable.date)]
    pd.concat([usable, rest]).to_csv(args.out, index=False)
    show = ["date", "rank", "score", "foam", "nearshore", "texture", "whitecaps", "cloudy"]
    print(f"\n{len(usable)} usable / {len(df)} frames. Truths:")
    print(usable[usable.truth][show].round(3).to_string(index=False))
    print(f"\nTop {args.top} candidates:")
    print(usable[~usable.truth].head(args.top)[show].round(3).to_string(index=False))


def robust_z(s):
    med = s.median()
    mad = (s - med).abs().median() * 1.4826 or 1e-9
    return (s - med) / mad


if __name__ == "__main__":
    main()
