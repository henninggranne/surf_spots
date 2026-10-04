"""Build a review page: truth frames + top candidates from a match_truths.py results file.

  python build_review.py --matches matches_2020.csv --year 2020 --title "Jomfruland Swell 2020" -o review_2020.html
Sea state comes from all hindcast_<year>.csv files unless --hindcast is given.
"""
import argparse
import base64
import glob
import json
from pathlib import Path

import pandas as pd

from match_truths import FRAME

BROWSER = ("https://browser.dataspace.copernicus.eu/?zoom=14&lat={lat:.5f}&lng={lng:.5f}"
           "&themeId=DEFAULT-THEME&datasetId=S2_L2A_CDAS&fromTime={d}T00:00:00.000Z"
           "&toTime={d}T23:59:59.999Z&layerId=1_TRUE_COLOR")


def hindcast_rows(paths):
    frames = [pd.read_csv(p, parse_dates=["time"]) for p in paths]
    h = pd.concat(frames).drop_duplicates("time")
    h = h[h.time.dt.hour == 10].copy()
    h["date"] = h.time.dt.strftime("%Y-%m-%d")
    return h.set_index("date")


# The exposed SE shore faces ~134 deg, so wind FROM ~314 deg (NW) blows straight offshore
OFFSHORE_FROM = 314


def wind_class(wdir, speed):
    """Wind relative to the shore, as surfers name it; strong wind flagged."""
    if wdir is None:
        return None
    a = abs((wdir - OFFSHORE_FROM + 180) % 360 - 180)
    name = ("Offshore" if a <= 30 else "Cross-offshore" if a <= 67 else "Cross-shore"
            if a <= 113 else "Cross-onshore" if a <= 150 else "Onshore")
    good = a <= 67
    if speed is not None and speed >= 10:
        name, good = name + ", strong", False
    return dict(name=name, good=good)


def num(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return None if v != v else round(v, 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=24)
    ap.add_argument("--hindcast", nargs="*", default=sorted(glob.glob("hindcast_20??.csv")))
    ap.add_argument("--year", default="2025", help="year shown in the page text")
    ap.add_argument("--title", default="Jomfruland Swell Check")
    ap.add_argument("--extra", nargs="*", default=[],
                    help="unranked dates to add anyway (e.g. partly cloudy frames worth a look)")
    ap.add_argument("--matches", default="matches.csv", help="results file from match_truths.py")
    ap.add_argument("-o", "--out", default="review.html")
    args = ap.parse_args()

    allm = pd.read_csv(args.matches)
    m = allm.dropna(subset=["rank"]).sort_values("rank")
    extra = allm[allm.date.isin(args.extra) & ~allm.date.isin(m.date)]
    picks = pd.concat([m[m.truth], m[~m.truth].head(args.top), extra])
    h = hindcast_rows([p for p in args.hindcast if Path(p).exists()])
    lat, lng = (FRAME[1] + FRAME[3]) / 2, (FRAME[0] + FRAME[2]) / 2

    items = []
    for _, r in picks.iterrows():
        d = r.date
        hc = h.loc[d] if d in h.index else None
        g = (lambda c: num(hc[c]) if hc is not None and c in hc else None)
        hs = g("wave_height") if g("wave_height") is not None else g("era5_wave_height")
        items.append(dict(
            date=d, truth=bool(r.truth), rank=None if pd.isna(r["rank"]) else int(r["rank"]),
            foam=num(r.foam), texture=num(r.texture), nearshore=num(r.nearshore),
            hs=hs,
            tp=g("wave_period") if g("wave_period") is not None else g("era5_wave_period"),
            wdir=g("wave_direction") if g("wave_direction") is not None else g("era5_wave_direction"),
            wind=g("wind_speed_10m"), winddir=g("wind_direction_10m"), gust=g("wind_gusts_10m"),
            windclass=wind_class(g("wind_direction_10m"), g("wind_speed_10m")),
            whitecaps=num(r.get("whitecaps")),
            link=BROWSER.format(lat=lat, lng=lng, d=d),
            img="data:image/jpeg;base64," + base64.b64encode(Path(f"frames/{d}.jpg").read_bytes()).decode(),
        ))
    usable = len(m)
    tpl = Path(__file__).with_name("review_template.html").read_text()
    html = (tpl.replace("__DATA__", json.dumps(items))
               .replace("__USABLE__", str(usable))
               .replace("__TOP__", str(args.top))
               .replace("__YEAR__", args.year)
               .replace("__TITLE__", args.title))
    Path(args.out).write_text(html)
    print(f"wrote {args.out}: {len(items)} frames ({sum(i['truth'] for i in items)} truths)")


if __name__ == "__main__":
    main()
