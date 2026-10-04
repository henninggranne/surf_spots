# Project: finding unknown surf spots in the Oslofjord / Skagerrak coast

## Goal
Find undiscovered surf spots by combining historical swell, wave and wind data with
Sentinel-2 satellite imagery, instead of driving around checking. Surfline is only used
for forecasts of the known reference spot (Saltstein), which works on big Jomfruland days.

## Key findings so far
- Surfline has no official historical API. Unofficial endpoints (e.g. pysurfline) give forecast
  windows only. Use open hindcast data instead: Open-Meteo Marine API (ERA5-based waves),
  Open-Meteo Archive API (wind), NOAA NDBC buoys, Copernicus Marine.
- Sentinel-2 passes ~every 5 days, ~10-11 UTC over Norway; clouds remove many passes.
  At 10 m resolution swell lines and foam ARE visible on good days (user confirmed in the
  Copernicus Browser, e.g. Jomfruland on 2018-01-28 and 2026-04-04).
- Known reference: white water on the south-east shore of Jomfruland around
  58°50'23"N 9°33'57"E.

## What a good Jomfruland day looks like (from user-verified days, 2026-10-03)
- Recipe (18 Surf vs 91 No days, ERA5 waves at 10 UTC): swell from 210-265 deg is the
  strictest condition (all Surf days 217-260; NE swell is blocked by the island).
  Likely = Hs >= 1.5 m and Tp >= 5.5 s; Possible = Hs >= 1.0 m and Tp >= 5.0 s.
  Hs >= 1.2 m + Tp >= 5.5 s catches 14/18 Surf days and only 3/91 No days.
  Period matters: SW No days with 1-1.5 m were mostly short 4-5 s wind sea.
- Benchmark best day: 2018-01-28 (user's #1). Image frames/2018-01-28.jpg; Copernicus Browser:
  https://browser.dataspace.copernicus.eu/?zoom=14&lat=58.84600&lng=9.58100&themeId=DEFAULT-THEME&datasetId=S2_L2A_CDAS&fromTime=2018-01-28T00:00:00.000Z&toTime=2018-01-28T23:59:59.999Z&layerId=1_TRUE_COLOR
  At 10 UTC (satellite): Hs 2.9 m, Tp 7.1 s, from 237 deg; wind 5.6 m/s (20 kph) from 261 deg
  (W, cross-offshore), gusts 8. Through the day swell 2.8-3.2 m, 6.7-7.2 s, turning 232->248
  deg; wind stayed W but rose to ~10 m/s (gusts 15) by 15-16 UTC. ~80% of the foam was > 20 m
  from the beach. Surfline terms: ~2.9-3.2 m, 7-8 s, SW-WSW, 20-25 kph W in the morning.
- Wave period is the strongest single signal (ERA5 mean period at 10 UTC, all reviewed days):
  >= 7 s: 6 Surf / 0 Unsure / 0 No; 6.5-7 s: 4/0/0 (incl. 2024-02-01, changed to Surf);
  6-6.5 s: 5/3/2; 5.5-6 s: 5/4/4; < 5 s: 1/3/70. All 6.5 s+ days came from 227-243 deg
  (North Sea swell entering the Skagerrak); NE seas are always short-period chop.
  Tiers in recipe_days.py: Solid = SW + Hs >= 1.5 m + Tp >= 6.5 s (10/10 reviewed were Surf),
  Likely = Hs >= 1.5 m + Tp >= 5.5 s, Possible = Hs >= 1.0 m + Tp >= 5.0 s.
- Per full year 2018-2025: ~10 Solid, ~19 Likely, ~26 Possible days. Solid is a Nov-Feb thing
  (Jan 2.5, Feb 2.1, Dec 1.9, Nov 1.4 per month); Solid+Likely also Sep-Oct (~3/month).
  2020 was the biggest year (23 Solid), 2021 the quietest (2 Solid).
- Surfline vs our data (one week of Saltstein forecasts, 2026-10-03..10; plus ERA5 vs
  Open-Meteo forecast model over 2021-2026):
  - Height: Open-Meteo forecast ~0.87 x Surfline; ERA5 ~1.17 x forecast model, so ERA5 heights
    ~= Surfline heights.
  - Period: Surfline (peak period, primary swell) reads ~0.7-0.8 s longer than our mean period.
    Our 6.5 s ~= Surfline 7-7.5 s; our 5.5 s ~= Surfline 6-6.5 s.
  - Wind: matches for the first 2-3 forecast days, then the models diverge.
  - Small sample, mostly short-period seas; firm up with a big-swell week.
- Possible "caught a lull" No days: 2024-04-14 (2.4 m, 6.4 s, cross-offshore), 2024-04-11.
- Wind decides quality. The exposed SE shore faces ~134 deg, so wind FROM ~314 deg (NW) is
  offshore. User: west to north-west wind looks "really groomed". Best days so far:
  2018-01-28 (2.9 m, W wind, cross-offshore) and 2018-09-23 (1.4 m, NW wind, offshore).
  SW wind is cross-shore (rougher); 10 m/s+ gives whitecaps.
- Sept-Oct is productive (5 surf days in 2018 alone), not only winter.
- A Sentinel-2 image is one moment: it can catch a lull between sets, so a good day can look
  modest (2026-04-04 looks far better on Google Earth). Don't treat weak foam as "no surf".
- Verdict meanings on the review pages: Surf = surf visible. Unsure = shore visible, might be
  surf, maybe not caught on a set. No = no surf. Can't see = cloud/haze/glint hides the shore.
- Sentinel-1 radar was tested and dropped (2026-10-03): shows wind roughness more than swell,
  passes at ~05/17 UTC, didn't separate surf from flat days. User chose Sentinel-2 only.
- Snow: the shoreline strip (first ~20 m) turns white on snowy flat days. Real foam spreads
  50-300 m out, so foam is measured from 20 m offshore outward. Snow days are kept, not dropped.

## Reading Surfline (Saltstein) for possible surf at Jomfruland
Rough guide built from the verified days and the Surfline offset above. Use the Primary Swell
column; Surfline's "Surf" number is breaking height at Saltstein, not the swell.
- Direction: primary swell from SW to WSW (about 210-265 deg). On Surfline's swell arrow that
  is the arrow pointing NE to ENE. Swell from NE, E or S does not reach the SE shore well.
- Size and period (primary swell):
  - Solid: >= 1.5 m and >= 7 s (every comparable day we checked was Surf)
  - Likely: >= 1.5 m and 6-7 s
  - Possible: >= 1.0 m and >= 6 s, or >= 1.5 m at 5 s (grey zone: wind and luck decide)
  - Under 5 s or under 1 m: usually nothing.
- Wind (the shore faces SE, so NW is straight offshore):
  - Best: from W to NW (Surfline arrow pointing E to SE), up to ~30-35 kph. User: west wind
    looks "really groomed". Best days: 2018-01-28 (W) and 2018-09-23 (NW).
  - OK but rougher: from SW (cross-shore).
  - Poor: from S to E (onshore), or 36+ kph (10 m/s) from any side.
- Example: Surfline 5 Oct 2026 showed 2.1 m / 7 s primary swell with 46-50 kph wind from SW:
  Solid swell, but strong cross-shore wind, so big and messy.

## Planned method
1. Pull hindcast wave + wind for known good days and find the recipe
   (Hs, period, swell/wind-wave direction, wind direction and speed).
2. Score the satellite archive for swell texture + foam, calibrated on the known days.
3. Score other coast stretches by geometry: exposure to the recipe swell direction,
   island shadowing, offshore wind angle. ON HOLD (user, 2026-10-03): seabed matters most.
   Much of e.g. Østfold faces the right way but the coastline/seabed gives poor waves, so
   bathymetry (step 4) has to come first or together with this step.
4. Add bathymetry (Kartverket, EMODnet) to look for reefs, bars and shelves.
5. Rank candidate spots, then verify on Sentinel-2 / aerial imagery on recipe days.
   Local wind-wave fetch matters in the Oslofjord, not just ocean swell.
Planned later: list all recipe days from wave data alone (incl. cloudy days) once there are
~15-20 verified good days.

## Files
README.md describes every file for the user; keep it in sync when files change.
- forecast_check.py: next-days outlook from the Open-Meteo forecast, converted to ERA5 scale
  (height / 0.85, period - 0.1 s, direction + 13 deg) and run through the recipe levels from
  recipe_days.py; also prints approximate Surfline numbers.
- fetch_hindcast.py: hourly waves + wind CSV for a range (hindcast_2018..2026.csv, full years).
  Wave point (58.78, 9.60), wind point (58.84, 9.57). Default marine model has no waves before
  ~2022, so it also pulls era5_ocean (era5_* columns, 0.5 deg grid, no swell split).
- cdse.py: CDSE Auth + endpoints + SCL cloud classes. secret.txt holds the OAuth client
  ("client ID: ..." / "client secret: ..."), used when env vars are unset. Never print or
  publish it.
- match_truths.py (current approach): fixed frame = user's Copernicus Browser view
  (9.540-9.622E, 58.830-58.862N, 472x356 px). Downloads RGB+NIR per pass (cache_frame/,
  frames/*.jpg). Use --max-cloud 101 (tile cloud % hides clear gaps over the island).
  Scores foam + near-shore brightening + swell texture on the exposed SE side; drops frames with
  bright patches offshore (missed cloud). SCL marks white water as cloud/snow, so cloud blobs
  within 300 m of shore are ignored. Also measures whitecaps (small specks far offshore).
  `--out matches_<year>.csv`.
- build_review.py + review_template.html -> review page per year (`--matches`, `--year`,
  `--title`, `--extra` for unranked dates). Cards show sea state, wind-to-shore label and
  image measures. Answers saved in each page's db collection "labels" (doc id = date,
  verdict yes/maybe/no/cantsee); read them with ArtifactData.
  - 2025: https://claude.ai/artifact/1Tu2RWDYWzVvjtuxExz4UH (review.html)
  - 2024: https://claude.ai/artifact/YAw1fk8cEYNnpNz19XzasK (review_2024.html)
  - 2018: https://claude.ai/artifact/9go3Ei1E7zd5jyPQM96ejn (review_2018.html)
  - 2019: https://claude.ai/artifact/57sDi2UsrPhQsep6Fg6Tx3 (review_2019.html)
  - 2020: https://claude.ai/artifact/2qKdiNDocHsKQSwHKNLtjf (review_2020.html)
  - 2021-2023 recipe days only: https://claude.ai/artifact/6QocVeXYmhsSX6mknP5QMG
    (review_2021_2023.html; match_truths.py --recipe recipe_days.csv downloads only those dates)
- surfline_vs_openmeteo_2026-10-03.csv: Surfline screenshot values vs Open-Meteo forecast.
- verdicts/<year>/labels/*.json: local copies of the review-page answers (ArtifactData out_dir).
  verdicts_conditions.csv = verdicts joined with wave/wind at 10 UTC.
- recipe_days.py -> recipe_days.csv: every day 2018-2026 matching the recipe for >= 3 daylight
  hours (07-16 UTC), with peak waves, wind-to-shore label, clear-image flag and verdict.
- Ranking page (user's order of the first 10 Surf days): https://claude.ai/artifact/TtJ58EtZamuLHWySNvvkkX
  (db "ranking/order"). User stopped ranking (too many days); its build files were deleted.
- sheets/: contact sheets for the user to open in the IDE.
- Deleted 2026-10-03 as no longer needed: find_swell_days.py (old whole-area scoring) with
  cache/, previews/, scores.csv; s1_frames.py + Sentinel-1 data; ranking build files;
  hindcast.csv, hindcast_s1.csv, matches.csv.

## Status (2026-10-03)
- Truths used for ranking: 2018-01-28, 2026-04-04, 2025-11-29, 2025-02-05.
- User verdicts:
  - 2025 Surf: 11-29, 02-05. Unsure: 01-14, 01-19, 06-30, 07-03. Can't see: 10-03.
  - 2018 Surf: 09-13, 09-20, 09-23 (top tier), 09-30, 10-23. Unsure: 10-03, 10-10.
  - 2019 Surf: 08-19, 10-28. 2020 Surf: 01-03, 01-08, 01-16, 02-22 (4.2 m), 03-11, 11-03
    (user: "proper good days in 2020, many top 10").
  - 2024 Surf: 02-04, 02-01 (changed from Unsure by user). Unsure: 01-25, 09-11. (04-11 = No.)
  - 2021-2023 Surf: 2021-10-27, 2022-02-06, 2022-11-11, 2023-10-14 (3.7 m, 7.2 s).
    Unsure: 2021-02-26, 2021-11-11, 2022-11-06, 2022-12-18, 2023-02-21.
  - Only 12 of 50 recipe days in 2021-2023 with a Sentinel-2 pass had a clear view (clouds).
- User's ranking of first 10 (images only, timing luck matters): 2018-01-28, 2018-09-23,
  2024-02-04, 2018-09-20, 2025-02-05, 2025-11-29, 2018-09-13, 2026-04-04, 2018-10-23, 2018-09-30.
- Images give yes/no (and "at least this good" when a set is caught); quality comes from
  conditions. Pending idea: rank candidates by foam only (matched 2018 verdicts best).
- Next: step 3 is on hold until bathymetry is in. Ideas: more Surfline screenshots on a
  big-swell week to firm up the offset; bathymetry for Jomfruland first to learn what
  seabed makes it work.

## Notes
- User is in Oslo (Europe/Oslo). Speaks English; may write quickly with typos.
- Keep explanations practical and short.
- User wants to approve each step (manual mode): propose commands, edits, downloads and
  publishes, say what they do, then wait for a yes.
