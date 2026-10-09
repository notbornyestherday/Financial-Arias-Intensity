# Decision log

Departures from the project brief and choices the brief left open. Newest last. Each entry:
what, why, and what it affects.

| ID | Date | Decision | Why |
|---|---|---|---|
| D-001 | 2026-10-06 | Sample extended from 2024 to 2025-12. | April 2025 tariff selloff and the April 9 pause rally give a headline-driven burst (a stress test for H1). Also gives a longer out-of-sample window at no extra data cost. |
| D-002 | 2026-10-06 | First bar of the day contributes ln(close/open) of that bar. | Keeps the opening burst (2015-08-24) and excludes the overnight gap. |
| D-003 | 2026-10-06 | A return spanning k minutes (halt, missing bar) is assigned to the minute it ends in and deseasonalized by sqrt(sum of s^2) over those k minutes. | Energy is neither lost nor inflated across halts. |
| D-004 | 2026-10-06 | Seasonality uses prior days only, single-minute returns only, and skips half-days. | No look-ahead. Multi-minute returns and half-day closes would distort s(tau). |
| D-005 | 2026-10-06 | Suspected bad prints are flagged, not deleted. H1 is run with them removed; everything is reported both ways. | D5-95 and W50 are far more sensitive to one bad minute than RV is. |
| D-006 | 2026-10-06 | `tests_vix.py` renamed `src/fai/vix.py`. | Avoids confusion with unit tests in `tests/`. |
| D-007 | 2026-10-06 | Calendar module named `sessions.py`. | Avoids shadowing the stdlib `calendar` module. |
| D-008 | 2026-10-06 | H1 split into H1a (events), H1b (reversal, full sample) and H1c (FOMC positive control). H2 split into H2a (weighting, including a control for unweighted FAI) and H2b (concentration). VIX changes in logs. | As written in the brief, H1 had n=3 and an information-arrival confound. The headline measure faced no predictive test. H2 could not separate the liquidity weighting from the deseasonalizing. |
| D-009 | 2026-10-09 | Primary concentration measure is W50: the shortest time the Husid curve takes to climb 50 points. D5-75 (seismology standard) is secondary and every W50 test is repeated with it; D5-95 is reported for comparison. | All three are Husid-curve durations. A trading day has a constant background energy rate, so a start fixed at H = 5% falls in background; W50 lets the start float. Simulation (`scripts/sim_duration_power.py`, 1000 reps), separation d between a burst and a same-RV grind, D5-95 / D5-75 / W50: x12 4.1 / 6.4 / 24.9; x6 3.0 / 6.4 / 9.9; x4 2.0 / 3.3 / 3.7; x6 with t(4) noise 1.7 / 3.0 / 4.5. |
| D-010 | 2026-10-06 | Request raw (unadjusted) prices from the vendor. | Dollar volume in Amihud should be real. Intraday log returns are unaffected either way. |
| D-011 | 2026-10-09 | Preliminary H1b null check passed. | With independent increments and concentration varying across days (16,000 days, normal and t(4) noise), slopes of VR(30/5) on ln W50, ln D5-75 and ln D5-95 were all within about 2 SE of zero with mixed signs (`scripts/sim_h1b_null.py`). The VR test is not mechanically tied to concentration in this setting. |
| D-012 | 2026-10-09 | HYPOTHESES file renamed to HYPOTHESES.md; H3 formula restored. | Both were altered by a Notion export (ID suffix on the file name; underscores turned into asterisks). No change in substance. Pre-registration commit: 0c666cb, 2026-10-09 11:57 ET. |
## Open questions

- Vendor (Alpha Vantage vs. FirstRate) and bar timestamp convention. Confirm the convention from the vendor docs and from `run_all.py --stages ingest` diagnostics.
- Smooth s(tau) across neighbouring minutes? Each per-minute estimate rests on about 60 observations.
- RMS vs. median seasonality as the default. One crash day inflates RMS s(tau) at that minute for 60 days.
- Should R_m skip half-days?
- Fill `ref/fomc_dates.csv`.
- Week 2: repeat the H1b null check (D-011) on the full pipeline, with bid-ask bounce and estimated seasonality.
