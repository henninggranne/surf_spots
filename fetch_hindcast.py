"""Fetch hourly wave + wind hindcast near Jomfruland and save to CSV.

Examples:
  python fetch_hindcast.py 2018-01-28 2026-04-04            # specific days
  python fetch_hindcast.py --range 2017-03-01 2026-10-01    # whole period (-> hindcast.csv)

Data: Open-Meteo Marine API (wave/swell) + Open-Meteo Archive API (wind, ERA5).
Free for non-commercial use. Times are UTC (Sentinel-2 passes Norway ~10-11 UTC).
"""
import argparse
import datetime as dt

import pandas as pd
import requests

MARINE = "https://marine-api.open-meteo.com/v1/marine"
ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"

# Offshore point south-east of Jomfruland (marine model grid is coarse, so stay off the coast)
WAVE_PT = (58.78, 9.60)
# Coastal point for wind
WIND_PT = (58.84, 9.57)

WAVE_VARS = ",".join([
    "wave_height", "wave_period", "wave_direction",
    "wind_wave_height", "wind_wave_period", "wind_wave_direction",
    "swell_wave_height", "swell_wave_period", "swell_wave_direction",
])
WIND_VARS = "wind_speed_10m,wind_direction_10m,wind_gusts_10m"


def _get(url, params):
    r = requests.get(url, params=params, timeout=120)
    r.raise_for_status()
    h = r.json()["hourly"]
    df = pd.DataFrame(h)
    df["time"] = pd.to_datetime(df["time"])
    return df


def fetch(start, end):
    waves = _get(MARINE, dict(latitude=WAVE_PT[0], longitude=WAVE_PT[1], start_date=start,
                              end_date=end, hourly=WAVE_VARS, timezone="UTC"))
    # Default marine model has no data before ~2022; ERA5 ocean covers all years (0.5 deg grid,
    # no swell/wind-wave split), so add it as era5_* columns for a consistent long series.
    era5 = _get(MARINE, dict(latitude=WAVE_PT[0], longitude=WAVE_PT[1], start_date=start,
                             end_date=end, hourly="wave_height,wave_period,wave_direction",
                             models="era5_ocean", timezone="UTC"))
    waves = waves.merge(era5.add_prefix("era5_").rename(columns={"era5_time": "time"}),
                        on="time", how="outer")
    wind = _get(ARCHIVE, dict(latitude=WIND_PT[0], longitude=WIND_PT[1], start_date=start,
                              end_date=end, hourly=WIND_VARS, wind_speed_unit="ms",
                              timezone="UTC"))
    return waves.merge(wind, on="time", how="outer")


def chunks(start, end):
    s, e = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
    while s <= e:
        nxt = min(dt.date(s.year, 12, 31), e)
        yield s.isoformat(), nxt.isoformat()
        s = nxt + dt.timedelta(days=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dates", nargs="*", help="specific YYYY-MM-DD days")
    ap.add_argument("--range", nargs=2, metavar=("START", "END"))
    ap.add_argument("-o", "--out", default="hindcast.csv")
    args = ap.parse_args()

    frames = []
    if args.range:
        for s, e in chunks(*args.range):
            print(f"fetching {s} .. {e}")
            frames.append(fetch(s, e))
    for d in args.dates:
        print(f"fetching {d}")
        frames.append(fetch(d, d))
    if not frames:
        ap.error("give dates or --range")

    df = pd.concat(frames).drop_duplicates("time").sort_values("time")
    df.to_csv(args.out, index=False)
    print(f"saved {len(df)} rows -> {args.out}")

    # Quick look at the satellite-pass hours for any explicit days
    for d in args.dates:
        sub = df[(df.time.dt.strftime("%Y-%m-%d") == d) & df.time.dt.hour.isin([10, 11])]
        print(f"\n{d} (10-11 UTC)")
        print(sub.drop(columns=["time"]).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
