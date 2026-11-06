# H1 results (registered tests, full sample)

Written by `scripts/h1_tests.py`. How each outcome is read was fixed in advance in `paper/interpretation_table.md`. Exploratory follow-ups named there are not in this run; nor is the D-025 version without Fed Chair appearances.

## Primary: flagged prints removed

3,989 test days (2010-01-04 to 2025-12-31), of which 130 FOMC days.

### Verdicts

- H1a: crash days q < 10: False; median q of the 2020 halt days 56.4 (> 50: True). H1a is falsified (with D5-75: falsified; median q of the 2020 days 83.1). Without the first 30 minutes: median q 55.6.
- H1b (VR** on ln W50): not significant. With D5-75: not significant.
- H1c: FOMC days more concentrated: supported, but fragile (D5-75 disagrees) (with D5-75: not significant); FOMC dummy in the H1b regression: not significantly negative (holds). H1c holds on W50, and is fragile under the robustness rule.

Verdicts use raw two-sided tests at 5% (D-029). H1b and H1c concentration belong to the seven-test Holm family, adjusted once the H2 results exist; the H1c dummy is reported raw.

### H1a: named days

| day | RV | RV decile | W50 (min) | q | D5-75 (min) | q (D5-75) | W50 without open | q without open |
|---|---|---|---|---|---|---|---|---|
| 2010-05-06 | 0.00227 | 10 | 4.4 | 0.3 | 42.8 | 0.3 | 4.4 | 0.3 |
| 2015-08-24 | 0.00128 | 10 | 171.5 | 87.0 | 336.4 | 100.0 | 137.6 | 54.1 |
| 2020-03-09 | 0.00105 | 10 | 170.1 | 85.2 | 295.0 | 89.2 | 150.8 | 75.2 |
| 2020-03-12 | 0.00275 | 10 | 46.9 | 5.3 | 221.4 | 15.0 | 40.8 | 3.5 |
| 2020-03-16 | 0.00256 | 10 | 149.8 | 59.1 | 280.1 | 76.9 | 140.9 | 59.9 |
| 2020-03-18 | 0.00288 | 10 | 145.9 | 53.6 | 296.5 | 90.5 | 134.0 | 51.4 |

### H1b and H1c regressions

| test | y | x | coef | se | t | p | n | lag |
|---|---|---|---|---|---|---|---|---|
| H1b | VR** (primary) | ln W50 | -0.0083 | 0.0151 | -0.55 | 0.583 | 3859 | 9 |
| H1b | VR** (primary) | ln D5-75 | +0.0289 | 0.0287 | +1.01 | 0.314 | 3859 | 9 |
| H1b | VR** (primary) | ln D5-95 | +0.0176 | 0.0648 | +0.27 | 0.786 | 3859 | 9 |
| H1b | VR(30/5) (registered) | ln W50 | -0.0260 | 0.0302 | -0.86 | 0.390 | 3859 | 9 |
| H1b | VR(30/5) (registered) | ln D5-75 | +0.1722 | 0.0513 | +3.35 | 0.001 | 3859 | 9 |
| H1b | VR(30/5) (registered) | ln D5-95 | +0.0269 | 0.1600 | +0.17 | 0.866 | 3859 | 9 |
| H1b | VR* | ln W50 | -0.0050 | 0.0196 | -0.26 | 0.798 | 3859 | 9 |
| H1b | VR* | ln D5-75 | +0.0748 | 0.0367 | +2.04 | 0.041 | 3859 | 9 |
| H1b | VR* | ln D5-95 | +0.0035 | 0.0936 | +0.04 | 0.971 | 3859 | 9 |
| H1b | VR*(60/10) | ln W50 | -0.0395 | 0.0279 | -1.41 | 0.157 | 3859 | 9 |
| H1b | VR*(60/10) | ln D5-75 | +0.1295 | 0.0463 | +2.79 | 0.005 | 3859 | 9 |
| H1b | VR*(60/10) | ln D5-95 | +0.0208 | 0.1224 | +0.17 | 0.865 | 3859 | 9 |
| H1c concentration | ln W50 | FOMC | -0.8835 | 0.0610 | -14.48 | 0.000 | 3989 | 9 |
| H1c concentration | ln D5-75 | FOMC | -0.0539 | 0.0341 | -1.58 | 0.114 | 3989 | 9 |
| H1c dummy | VR** (primary) | FOMC (with ln W50) | -0.0426 | 0.0313 | -1.36 | 0.174 | 3989 | 9 |
| H1c dummy | VR** (primary) | FOMC (with ln D5-75) | -0.0293 | 0.0283 | -1.04 | 0.299 | 3989 | 9 |

## Flagged prints kept

3,989 test days (2010-01-04 to 2025-12-31), of which 130 FOMC days.

### Verdicts

- H1a: crash days q < 10: False; median q of the 2020 halt days 56.4 (> 50: True). H1a is falsified (with D5-75: falsified; median q of the 2020 days 83.0). Without the first 30 minutes: median q 55.6.
- H1b (VR** on ln W50): not significant. With D5-75: not significant.
- H1c: FOMC days more concentrated: supported, but fragile (D5-75 disagrees) (with D5-75: not significant); FOMC dummy in the H1b regression: not significantly negative (holds). H1c holds on W50, and is fragile under the robustness rule.

Verdicts use raw two-sided tests at 5% (D-029). H1b and H1c concentration belong to the seven-test Holm family, adjusted once the H2 results exist; the H1c dummy is reported raw.

### H1a: named days

| day | RV | RV decile | W50 (min) | q | D5-75 (min) | q (D5-75) | W50 without open | q without open |
|---|---|---|---|---|---|---|---|---|
| 2010-05-06 | 0.00227 | 10 | 4.4 | 0.3 | 42.8 | 0.3 | 4.4 | 0.3 |
| 2015-08-24 | 0.00128 | 10 | 171.5 | 87.0 | 336.4 | 100.0 | 137.6 | 54.1 |
| 2020-03-09 | 0.00105 | 10 | 170.1 | 85.2 | 295.0 | 89.2 | 150.8 | 75.2 |
| 2020-03-12 | 0.00275 | 10 | 46.9 | 5.3 | 221.4 | 15.0 | 40.8 | 3.5 |
| 2020-03-16 | 0.00256 | 10 | 149.8 | 59.1 | 280.1 | 76.7 | 140.9 | 59.9 |
| 2020-03-18 | 0.00288 | 10 | 145.9 | 53.6 | 296.5 | 90.5 | 134.0 | 51.4 |

### H1b and H1c regressions

| test | y | x | coef | se | t | p | n | lag |
|---|---|---|---|---|---|---|---|---|
| H1b | VR** (primary) | ln W50 | -0.0083 | 0.0151 | -0.55 | 0.580 | 3859 | 9 |
| H1b | VR** (primary) | ln D5-75 | +0.0287 | 0.0287 | +1.00 | 0.318 | 3859 | 9 |
| H1b | VR** (primary) | ln D5-95 | +0.0173 | 0.0647 | +0.27 | 0.789 | 3859 | 9 |
| H1b | VR(30/5) (registered) | ln W50 | -0.0261 | 0.0302 | -0.86 | 0.388 | 3859 | 9 |
| H1b | VR(30/5) (registered) | ln D5-75 | +0.1721 | 0.0514 | +3.35 | 0.001 | 3859 | 9 |
| H1b | VR(30/5) (registered) | ln D5-95 | +0.0269 | 0.1600 | +0.17 | 0.867 | 3859 | 9 |
| H1b | VR* | ln W50 | -0.0051 | 0.0196 | -0.26 | 0.795 | 3859 | 9 |
| H1b | VR* | ln D5-75 | +0.0746 | 0.0367 | +2.03 | 0.042 | 3859 | 9 |
| H1b | VR* | ln D5-95 | +0.0033 | 0.0936 | +0.03 | 0.972 | 3859 | 9 |
| H1b | VR*(60/10) | ln W50 | -0.0396 | 0.0279 | -1.42 | 0.156 | 3859 | 9 |
| H1b | VR*(60/10) | ln D5-75 | +0.1296 | 0.0464 | +2.80 | 0.005 | 3859 | 9 |
| H1b | VR*(60/10) | ln D5-95 | +0.0209 | 0.1224 | +0.17 | 0.864 | 3859 | 9 |
| H1c concentration | ln W50 | FOMC | -0.8836 | 0.0610 | -14.48 | 0.000 | 3989 | 9 |
| H1c concentration | ln D5-75 | FOMC | -0.0539 | 0.0341 | -1.58 | 0.114 | 3989 | 9 |
| H1c dummy | VR** (primary) | FOMC (with ln W50) | -0.0427 | 0.0313 | -1.36 | 0.173 | 3989 | 9 |
| H1c dummy | VR** (primary) | FOMC (with ln D5-75) | -0.0294 | 0.0283 | -1.04 | 0.299 | 3989 | 9 |
