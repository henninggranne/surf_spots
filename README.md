# Jomfruland surf spots

Finding good surf days, and later new surf spots, on the Skagerrak coast by combining
Sentinel-2 satellite images with historical wave and wind data.

So far the work covers one spot: the exposed south-east shore of Jomfruland (Kragerø).
Satellite images from 2018–2025 were checked by eye, and the verified surf days were used to
find a "recipe": the swell, period and wind that give surf there.

## The recipe in short

| Level | Swell direction | Height | Period (our data) | ≈ Surfline period |
|---|---|---|---|---|
| **Solid** | SW–WSW, 210–265° | ≥ 1.5 m | ≥ 6.5 s | ≈ 7 s+ |
| Likely | SW–WSW, 210–265° | ≥ 1.5 m | ≥ 5.5 s | ≈ 6–7 s |
| Possible | SW–WSW, 210–265° | ≥ 1.0 m | ≥ 5.0 s | ≈ 6 s |

- Period matters most: every reviewed day at 6.5 s or more was a surf day.
- Wind decides quality. The shore faces south-east, so **W to NW wind is offshore** and grooms
  the waves. SW wind blows along the shore, and 10 m/s (36 kph) or more is too much.
- About 10 Solid days a year, mostly November to February.

More detail, including how to read a Surfline forecast for Jomfruland, is in
[CLAUDE.md](CLAUDE.md).

## Benchmark: the best day, 28 January 2018

The best day found so far, ranked #1 by eye. Use it as the reference for what "pumping" looks
like at Jomfruland.

- Satellite image: [frames/2018-01-28.jpg](frames/2018-01-28.jpg), or the same view in
  [Copernicus Browser](https://browser.dataspace.copernicus.eu/?zoom=14&lat=58.84600&lng=9.58100&themeId=DEFAULT-THEME&datasetId=S2_L2A_CDAS&fromTime=2018-01-28T00:00:00.000Z&toTime=2018-01-28T23:59:59.999Z&layerId=1_TRUE_COLOR)
  (Sentinel-2 pass about 10:30 UTC, 11:30 local time)
- What the image shows: thick white water along the whole SE shore, reaching far out (about 80%
  of the foam was more than 20 m from the beach), and clean swell lines offshore.

Conditions (ERA5 waves, Open-Meteo wind; times in UTC, local time is UTC+1 in winter):

| UTC | Waves | Period | Swell from | Wind | Gusts | Wind vs shore |
|---|---|---|---|---|---|---|
| 08:00 | 2.9 m | 6.8 s | 234° SW | 5.4 m/s from 258° W | 8.5 | cross-offshore |
| **10:00** (satellite) | **2.9 m** | **7.1 s** | **237° SW** | **5.6 m/s from 261° W** | **8.1** | **cross-offshore** |
| 12:00 | 3.1 m | 7.1 s | 241° WSW | 7.4 m/s from 271° W | 11.1 | cross-offshore |
| 14:00 | 3.2 m | 7.0 s | 245° WSW | 9.1 m/s from 269° W | 13.5 | cross-offshore |
| 16:00 | 3.0 m | 6.9 s | 248° WSW | 9.8 m/s from 275° W | 14.9 | cross-offshore, strong |

In Surfline terms that is roughly **2.9–3.2 m primary swell at 7–8 s from SW–WSW, with
20–25 kph wind from the west** in the morning. That's a Solid day with a groomed morning; the
wind picked up to about 35 kph by the afternoon.

## Everyday use

Check the coming week:

```
.venv/bin/python forecast_check.py
.venv/bin/python forecast_check.py --days 10 --hourly
```

It prints one line per day with the level (Solid / Likely / Possible / -), waves, roughly
what Surfline would show, wind and whether the wind is offshore.

## Scripts

Run everything from this folder with `.venv/bin/python <script>`.

| Script | What it does | Writes |
|---|---|---|
| `forecast_check.py` | Surf outlook for the next days: Open-Meteo forecast + the recipe. | prints only |
| `fetch_hindcast.py` | Downloads hourly wave and wind history from Open-Meteo (free, no login). `--range 2024-01-01 2024-12-31 -o hindcast_2024.csv` | `hindcast_<year>.csv` |
| `match_truths.py` | Lists Sentinel-2 passes over the Jomfruland frame, downloads a small image per pass, measures white water on the SE shore, removes cloudy frames and ranks the rest. Needs the Copernicus login. `--year 2020 --max-cloud 101 --out matches_2020.csv`; `--recipe recipe_days.csv` fetches only recipe days. | `cache_frame/`, `frames/`, `matches_<year>.csv` |
| `build_review.py` | Turns a results file into a review page with images, sea state, wind label and Surf / Unsure / No / Can't see buttons. Uses `review_template.html`. | `review_<year>.html` |
| `recipe_days.py` | Labels every day since 2018 as Solid / Likely / Possible from the wave data, counts days per year and month, and checks the labels against your verdicts. | `recipe_days.csv` |
| `cdse.py` | Shared Copernicus Data Space login and addresses, used by `match_truths.py`. | – |

## Data and results

| File / folder | Contents |
|---|---|
| `hindcast_<year>.csv` | Hourly waves and wind 2018–2026. Use the `era5_*` wave columns for comparisons across years (the default model has no data before ~2022). |
| `cache_frame/` | Downloaded Sentinel-2 data per pass (~640 MB). Keep it: re-scoring is free from here, re-downloading is not. |
| `frames/` | True-colour JPEG of every pass, e.g. `frames/2020-01-08.jpg`. |
| `matches_<year>.csv` | Image scores per pass: foam, near-shore brightness, texture, cloud, rank. |
| `verdicts/<year>/labels/` | Your answers from the review pages, one small JSON file per day. |
| `verdicts_conditions.csv` | Your verdicts joined with waves and wind at 10 UTC. |
| `recipe_days.csv` | Every recipe day 2018–2026 with level, peak waves, wind label, clear image yes/no, verdict. |
| `surfline_vs_openmeteo_2026-10-03.csv` | Surfline screenshot values vs Open-Meteo for the same hours. |
| `review*.html` | Local copies of the published review pages (`review.html` is 2025). |
| `sheets/` | Side-by-side image sheets to open in the editor. |
| `secret.txt` | Copernicus login. Private: never share or commit it. |

## Review pages (claude.ai, private)

| Year | Link |
|---|---|
| 2018 | https://claude.ai/artifact/9go3Ei1E7zd5jyPQM96ejn |
| 2019 | https://claude.ai/artifact/57sDi2UsrPhQsep6Fg6Tx3 |
| 2020 | https://claude.ai/artifact/2qKdiNDocHsKQSwHKNLtjf |
| 2021–2023 (recipe days only) | https://claude.ai/artifact/6QocVeXYmhsSX6mknP5QMG |
| 2024 | https://claude.ai/artifact/YAw1fk8cEYNnpNz19XzasK |
| 2025 | https://claude.ai/artifact/1Tu2RWDYWzVvjtuxExz4UH |
| Your top-10 ranking | https://claude.ai/artifact/TtJ58EtZamuLHWySNvvkkX |

## Adding a new year

```
.venv/bin/python fetch_hindcast.py --range 2017-01-01 2017-12-31 -o hindcast_2017.csv
.venv/bin/python match_truths.py --year 2017 --max-cloud 101 --truth 2018-01-28 2026-04-04 2025-11-29 2025-02-05 --out matches_2017.csv
.venv/bin/python build_review.py --matches matches_2017.csv --year 2017 --title "Jomfruland Swell 2017" -o review_2017.html
```

Then publish the page, mark the days, and re-run `recipe_days.py`.

## Setup

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

The Copernicus login (free account at dataspace.copernicus.eu → OAuth client) goes in
`secret.txt` as two lines, `client ID: ...` and `client secret: ...`.

## Not done yet

- Other spots along the coast. On hold until seabed data (Kartverket, EMODnet) is in: plenty
  of coastline faces the right way but has a seabed that gives poor waves.
- The Surfline offset is based on one week of mostly small forecasts. A big-swell week would
  firm it up.
