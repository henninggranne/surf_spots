"""List every day that matches the Jomfruland surf recipe in the wave data, cloudy or not.

Recipe (from 18 verified Surf days vs 91 No days, 2026-10-03):
  Solid:    swell from 210-265 deg, Hs >= 1.5 m, Tp >= 6.5 s  (every reviewed 6.5 s+ day was Surf)
  Likely:   swell from 210-265 deg, Hs >= 1.5 m, Tp >= 5.5 s
  Possible: swell from 210-265 deg, Hs >= 1.0 m, Tp >= 5.0 s
A day counts when the recipe holds for >= 3 daylight hours (07-16 UTC).
Uses the ERA5 wave columns so every year compares like for like.

  python recipe_days.py            -> recipe_days.csv + summary per year and month
"""
import glob
import json

import pandas as pd

from build_review import wind_class

DIR = (210, 265)
LEVELS = {"Solid": (1.5, 6.5), "Likely": (1.5, 5.5), "Possible": (1.0, 5.0)}
HOURS = range(7, 17)
MIN_HOURS = 3


def load_hindcast():
    h = pd.concat([pd.read_csv(f, parse_dates=["time"]) for f in glob.glob("hindcast_20??.csv")])
    h = h.drop_duplicates("time").sort_values("time")
    h = h[h.time.dt.hour.isin(HOURS)].copy()
    h["date"] = h.time.dt.strftime("%Y-%m-%d")
    h["hs"], h["tp"], h["dir"] = h.era5_wave_height, h.era5_wave_period, h.era5_wave_direction
    return h


def load_verdicts():
    out = {"2018-01-28": "yes", "2026-04-04": "yes"}
    for f in glob.glob("verdicts/*/labels/*.json"):
        r = json.load(open(f))
        r = r.get("data", r)
        out[r["date"]] = r["verdict"]
    return out


def clear_frames():
    """Dates with a usable (clear) Sentinel-2 frame, from the match_truths results."""
    dates = set()
    for f in glob.glob("matches_20??.csv"):
        m = pd.read_csv(f)
        dates |= set(m.dropna(subset=["rank"]).date)
    return dates, {f[8:12] for f in glob.glob("matches_20??.csv")}


def main():
    h = load_hindcast()
    verdicts = load_verdicts()
    clear, imaged_years = clear_frames()

    rows = []
    for date, g in h.groupby("date"):
        sw = g.dir.between(*DIR)
        level = None
        for name, (hs, tp) in LEVELS.items():
            m = sw & (g.hs >= hs) & (g.tp >= tp)
            if m.sum() >= MIN_HOURS:
                level, hit = name, g[m]
                break
        if not level:
            continue
        peak = hit.loc[hit.hs.idxmax()]
        wc = wind_class(peak.wind_direction_10m, peak.wind_speed_10m)
        year = date[:4]
        rows.append(dict(
            date=date, level=level, hours=len(hit),
            hs=round(peak.hs, 1), tp=round(peak.tp, 1), dir=int(peak.dir),
            wind=round(peak.wind_speed_10m, 1), wind_from=int(peak.wind_direction_10m),
            shore=wc["name"], clean=wc["good"],
            image=("clear" if date in clear else "none/cloudy") if year in imaged_years else "not checked",
            verdict=verdicts.get(date, ""),
        ))
    d = pd.DataFrame(rows)
    d.to_csv("recipe_days.csv", index=False)

    d["year"] = d.date.str[:4]
    d["month"] = pd.to_datetime(d.date).dt.month
    print("Recipe days per year (clean = offshore or cross-offshore wind at the peak hour):")
    for y, g in d.groupby("year"):
        parts = []
        for lvl in LEVELS:
            s = g[g.level == lvl]
            parts.append(f"{len(s):3d} {lvl} ({s.clean.sum():2d} clean)")
        print(f"  {y}: " + "   ".join(parts))
    # Averages over full years only (the current year is still running)
    full = d[d.year < pd.Timestamp.now().strftime("%Y")]
    yrs = full.year.nunique()
    print(f"\nAverage per full year ({full.year.min()}-{full.year.max()}): " +
          ", ".join(f"{(full.level == lvl).sum() / yrs:.0f} {lvl}" for lvl in LEVELS))

    names = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
    for title, lv in [("Solid", ["Solid"]), ("Solid + Likely", ["Solid", "Likely"])]:
        s = full[full.level.isin(lv)]
        by_m = s.groupby("month").size().reindex(range(1, 13), fill_value=0) / yrs
        print(f"\n{title} days per month (average per year):")
        print("  " + "  ".join(f"{n} {v:3.1f}" for n, v in zip(names, by_m)))

    print("\nCheck against your verdicts (days with a clear image and a verdict):")
    for lvl in LEVELS:
        g = d[(d.level == lvl) & (d.verdict != "")]
        print(f"  {lvl:8s}: {(g.verdict == 'yes').sum()} Surf, {(g.verdict == 'maybe').sum()} Unsure, "
              f"{(g.verdict == 'no').sum()} No")

    print("\nLikely + clean wind + clear image but never reviewed (worth a look):")
    todo = d[(d.level == "Likely") & d.clean & (d.image == "clear") & (d.verdict == "")]
    print(todo[["date", "hs", "tp", "dir", "wind", "wind_from", "shore"]].to_string(index=False)
          if len(todo) else "  none")


if __name__ == "__main__":
    main()
