"""Surf outlook for the Jomfruland SE shore for the next days, using the verified recipe.

  python forecast_check.py            # next 7 days
  python forecast_check.py --days 10 --hourly

Fetches the Open-Meteo forecast (free, no login) at the same points as fetch_hindcast.py,
converts it to the ERA5 scale the recipe was built on, and applies the Solid/Likely/Possible
rules from recipe_days.py. Also shows roughly what Surfline (Saltstein) would display.

Conversions (measured 2026-10-03, see CLAUDE.md):
  ERA5     = forecast model: height / 0.85, period - 0.1 s, direction + 13 deg
  Surfline ~ forecast model: height / 0.87, period + 0.7 s (primary swell peak period)
"""
import argparse

import pandas as pd
import requests

from build_review import wind_class
from fetch_hindcast import WAVE_PT, WIND_PT
from recipe_days import DIR, LEVELS, MIN_HOURS

MARINE = "https://marine-api.open-meteo.com/v1/marine"
FORECAST = "https://api.open-meteo.com/v1/forecast"
DAYLIGHT = range(8, 18)  # local hours (Europe/Oslo), same span as the recipe's 07-16 UTC


def fetch(days):
    common = dict(timezone="Europe/Oslo", forecast_days=days)
    w = requests.get(MARINE, params=dict(latitude=WAVE_PT[0], longitude=WAVE_PT[1],
                     hourly="wave_height,wave_period,wave_direction", **common), timeout=60)
    a = requests.get(FORECAST, params=dict(latitude=WIND_PT[0], longitude=WIND_PT[1],
                     hourly="wind_speed_10m,wind_direction_10m,wind_gusts_10m",
                     wind_speed_unit="ms", **common), timeout=60)
    w.raise_for_status()
    a.raise_for_status()
    d = pd.DataFrame(w.json()["hourly"]).merge(pd.DataFrame(a.json()["hourly"]), on="time")
    d["time"] = pd.to_datetime(d.time)
    d = d.dropna(subset=["wave_height", "wave_period", "wave_direction"])
    # ERA5 scale for the recipe
    d["hs"] = d.wave_height / 0.85
    d["tp"] = d.wave_period - 0.1
    d["dir"] = (d.wave_direction + 13) % 360
    # Roughly what Surfline's primary swell column would say
    d["sl_hs"] = d.wave_height / 0.87
    d["sl_tp"] = d.wave_period + 0.7
    return d


def level_of(row):
    if not (DIR[0] <= row.dir <= DIR[1]):
        return None
    for name, (hs, tp) in LEVELS.items():
        if row.hs >= hs and row.tp >= tp:
            return name
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--hourly", action="store_true", help="also print every daylight hour")
    args = ap.parse_args()

    d = fetch(args.days)
    d = d[d.time.dt.hour.isin(DAYLIGHT)].copy()
    d["level"] = d.apply(level_of, axis=1)
    order = list(LEVELS)

    print("Jomfruland SE shore outlook (daylight 08-17 local). "
          "Levels need >= %d daylight hours.\n" % MIN_HOURS)
    print(f"{'Day':<11}{'Level':<10}{'Waves (ERA5 scale)':<22}{'~Surfline':<14}{'Wind at peak':<26}Shore")
    for day, g in d.groupby(d.time.dt.date):
        best = None
        for lvl in order:  # best level that holds for enough hours
            hits = g[g.level.isin(order[: order.index(lvl) + 1])]
            if len(hits) >= MIN_HOURS:
                best = lvl
                break
        peak = (hits if best else g).loc[(hits if best else g).hs.idxmax()]
        wc = wind_class(peak.wind_direction_10m, peak.wind_speed_10m)
        waves = f"{peak.hs:.1f} m {peak.tp:.1f} s {peak.dir:3.0f}°"
        sl = f"{peak.sl_hs:.1f} m {peak.sl_tp:.0f} s"
        wind = f"{peak.wind_speed_10m:.0f} m/s ({peak.wind_speed_10m * 3.6:.0f} kph) from {peak.wind_direction_10m:3.0f}°"
        print(f"{day.strftime('%a %d %b'):<11}{best or '-':<10}{waves:<22}{sl:<14}{wind:<26}{wc['name']}")
        if args.hourly:
            for _, r in g.iterrows():
                print(f"    {r.time:%H:%M}  {r.level or '-':<9}{r.hs:.1f} m {r.tp:.1f} s {r.dir:3.0f}°   "
                      f"wind {r.wind_speed_10m:.0f} m/s from {r.wind_direction_10m:3.0f}°")
    print("\nSolid = swell 210-265°, >= 1.5 m, >= 6.5 s (every reviewed day like this was Surf).")
    print("Best wind: W to NW, under ~10 m/s. SW is cross-shore (rougher).")


if __name__ == "__main__":
    main()
