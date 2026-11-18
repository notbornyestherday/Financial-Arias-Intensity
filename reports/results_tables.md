# Results tables

Written by `scripts/results_tables.py` from `reports/h1_results.csv`, `reports/h1_results.md` (H1a table) and `reports/h2_results.csv`; nothing is re-estimated. Primary run (flagged prints removed). LaTeX versions in `paper/tables/`.

### Table 1. Pre-registered tests and verdicts

| Test | Prediction | Estimate | 95% CI | t | p | Holm p | With D5-75 | Verdict |
|---|---|---|---|---|---|---|---|---|
| H1a: W50 percentile q, named days | q < 10 (crash days); 2020 median > 50 | 0.3, 87.0; 56.4 |  |  |  |  | Falsified | Falsified |
| H1b: VR\*\* on ln W50 | b > 0 | -0.0083 | [-0.038, +0.021] | -0.55 | 0.583 | 1.000 | t +1.01 | Not supported |
| H1c: ln W50 on FOMC | c < 0 | -0.8835 | [-1.003, -0.764] | -14.48 | <0.001 | <0.001 | t -1.58 | Supported; fragile |
| H1c: FOMC dummy in H1b | not signif. negative | -0.0426 | [-0.104, +0.019] | -1.36 | 0.174 | — | t -1.04, holds | Holds |
| H2a (i): ln FAI_w | β ≠ 0 | -0.0058 | [-0.011, -0.001] | -2.30 | 0.022 | 0.108 |  | Significant before Holm only |
| H2a (ii): ln FAI_w, with ln FAI | β ≠ 0 | -0.0074 | [-0.045, +0.030] | -0.39 | 0.698 | 1.000 |  | Not significant |
| H2b: ln W50 | β ≠ 0 | -0.0141 | [-0.026, -0.003] | -2.39 | 0.017 | 0.101 | t -1.66 | Significant before Holm only; fragile |
| H2a out of sample: ln FAI_w | CW p < 5%, R2_OS > 0 | -0.32% |  | +0.25 | 0.403 | 1.000 |  | Fails |
| H2b out of sample: ln W50 | CW p < 5%, R2_OS > 0 | -0.07% |  | +1.15 | 0.126 | 0.504 | p 0.219, fails | Fails |

Notes: Primary run (flagged prints removed). H1a (Table 2): q on 2010-05-06 and 2015-08-24, then the median over the four 2020 halt days; it fails on 2015-08-24: q 87.0. H1b and H1c (Table 3): Newey-West standard errors (lag 9), RV-decile fixed effects, 2010-2025; n = 3,859 for H1b (FOMC days out) and 3,989 for H1c; exp(c) = 0.41, so FOMC days' W50 is 0.41 times that of days with similar RV. H2 (Tables 4 and 5): next-day d ln VIX on X with ln RV, r, min(r, 0), d ln VIX and ln VIX (D-027), 2010-2018, n = 2,245, lag 7. Out of sample, 2019-2025 with coefficients fixed in sample (n = 1,743), the estimate is R2_OS = 1 - MSE(with X) / MSE(without X), and t and p are the Clark-West statistic and its one-sided p. Verdicts use the raw p at 5% (D-029). Holm p: adjusted over the seven tests that predict an effect; the H1c dummy passes by not rejecting and is not in the family. Significant before Holm only: significant on the raw p but not after adjustment for multiple tests, read as weaker evidence. With D5-75: the same test with D5-75 in place of W50; a W50 result that changes sign or loses significance there is fragile (HYPOTHESES.md). With flagged prints kept, no verdict changes; the largest change in any t statistic between the two runs is 0.01. The pre-registered negative-result condition (HYPOTHESES.md) is met: b in H1b is indistinguishable from zero, and H2a and H2b fail out of sample.

### Table 2. H1a: named days

| Day | Event | √RV (%) | W50 (min) | q | D5-75 (min) | q | W50, no open | q |
|---|---|---|---|---|---|---|---|---|
| 2010-05-06 | Flash Crash | 4.76 | 4.4 | 0.3 | 42.8 | 0.3 | 4.4 | 0.3 |
| 2015-08-24 | Aug 2015 selloff | 3.58 | 171.5 | 87.0 | 336.4 | 100.0 | 137.6 | 54.1 |
| 2020-03-09 | Market-wide halt | 3.24 | 170.1 | 85.2 | 295.0 | 89.2 | 150.8 | 75.2 |
| 2020-03-12 | Market-wide halt | 5.24 | 46.9 | 5.3 | 221.4 | 15.0 | 40.8 | 3.5 |
| 2020-03-16 | Market-wide halt | 5.06 | 149.8 | 59.1 | 280.1 | 76.9 | 140.9 | 59.9 |
| 2020-03-18 | Market-wide halt | 5.37 | 145.9 | 53.6 | 296.5 | 90.5 | 134.0 | 51.4 |
| Median, 2020 halt days |  |  |  | 56.4 |  | 83.1 |  | 55.6 |

Notes: q: percentile of the measure among test days in the same RV decile (low = concentrated). Predictions (HYPOTHESES.md): q < 10 on 2010-05-06 and 2015-08-24; median q > 50 over the four 2020 halt days; falsified if any part fails. √RV: the day's realized volatility in percent. Without the first 30 minutes: W50 with the first 30 minutes of every day left out (the RV deciles are unchanged), reported because three of the four 2020 halts came within minutes of the open. All six days are in RV decile 10 (the top). Illustrative: six days chosen in advance, a calibration check rather than a test.

### Table 3. H1b and H1c regressions

|  | ln W50 | ln D5-75 | ln D5-95 |
|---|---|---|---|
| *Panel A. H1b: reversal on concentration, b (FOMC days out)* | | | |
| VR\*\* (primary, D-024) | **-0.0083 (-0.55)** | +0.0289 (+1.01) | +0.0176 (+0.27) |
| VR(30/5) (registered) | -0.0260 (-0.86) | +0.1722 (+3.35) | +0.0269 (+0.17) |
| VR\* (D-023) | -0.0050 (-0.26) | +0.0748 (+2.04) | +0.0035 (+0.04) |
| VR\*(60/10) (D-024) | -0.0395 (-1.41) | +0.1295 (+2.79) | +0.0208 (+0.17) |
| *Panel B. H1c: FOMC days (positive control, FOMC days in)* | | | |
| ln measure on FOMC dummy, c | **-0.8835 (-14.48)** | -0.0539 (-1.58) | — |
| FOMC dummy in the H1b regression | **-0.0426 (-1.36)** | -0.0293 (-1.04) | — |

Notes: Coefficient (t). Newey-West standard errors (lag 9), RV-decile fixed effects, 2010-2025, half-days out. Panel A: n = 3,859; the column is the concentration measure on the right-hand side, the row the variance ratio on the left. Prediction b > 0 (a shorter window, more reversal). Panel B: n = 3,989; predictions c < 0, and the dummy not significantly negative. Bold: the registered primary test. VR** is the primary reversal measure (D-024); the registered VR(30/5), VR* and VR*(60/10) are reported alongside, not judged.

### Table 4. H2: next-day VIX, in sample (2010-2018)

| Test | X | β | t | p | 1 SD (%) |
|---|---|---|---|---|---|
| *Panel A. Main regression (D-027)* | | | | | |
| H2a (i) | ln FAI_w | **-0.0058** | -2.30 | 0.022 | -0.49 |
| H2a (ii) | ln FAI_w | **-0.0074** | -0.39 | 0.698 | — |
| H2b | ln W50 | **-0.0141** | -2.39 | 0.017 | -0.46 |
| H2b | ln D5-75 | -0.0202 | -1.66 | 0.098 | -0.30 |
| *Panel B. Registered regression, without ln VIX (reported alongside)* | | | | | |
| H2a (i) | ln FAI_w | -0.0022 | -0.94 | 0.347 | -0.19 |
| H2a (ii) | ln FAI_w | -0.0107 | -0.57 | 0.572 | — |
| H2b | ln W50 | -0.0164 | -2.96 | 0.003 | -0.54 |
| H2b | ln D5-75 | -0.0248 | -2.14 | 0.032 | -0.37 |
| *Panel C. Other liquidity weightings, D-027 (D-030; reported alongside)* | | | | | |
| H2a (i) | ln FAI_w (Corwin-Schultz) | -0.0056 | -2.31 | 0.021 | -0.51 |
| H2a (ii) | ln FAI_w (Corwin-Schultz) | -0.0322 | -0.93 | 0.352 | — |
| H2a (i) | ln FAI_c (floored 1/C) | -0.0040 | -2.39 | 0.017 | -0.44 |
| H2a (ii) | ln FAI_c (floored 1/C) | -0.0020 | -0.80 | 0.423 | — |

Notes: Next-day d ln VIX on X, 2010-2018, n = 2,245, Newey-West lag 7. Panel A, the main regression (D-027): controls ln RV, r, min(r, 0), d ln VIX and today's ln VIX (VIX mean-reverts, and the trailing normalization in FAI would otherwise carry that effect). Panel B: the regression as registered in HYPOTHESES.md, without ln VIX. H2a (ii) also includes unweighted ln FAI, so its β measures the liquidity weighting alone (ln FAI_w = ln FAI + ln f_bar). The ln D5-75 rows apply the robustness rule to H2b. 1 SD: 100 x β x SD(X), the change in next-day d ln VIX, roughly the % change in VIX, for a one-SD higher X; for ln W50 a negative value means a shorter window (a more concentrated day) is followed by a bigger VIX rise. None is shown for H2a (ii): with ln FAI held fixed, X can only move by the weighting, whose SD is about a tenth of ln FAI_w's (pivot check). Bold: the registered primary tests.

### Table 5. H2: next-day VIX, out of sample (2019-2025)

| Test | X | β (2010-2018) | MSE | R2_OS (%) | CW t | CW p | Verdict |
|---|---|---|---|---|---|---|---|
| *Panel A. Main regression (D-027)* | | | | | | | |
| H2a | ln FAI_w | -0.0058 | 0.006105 | -0.32 | +0.25 | 0.403 | Fails |
| H2b | ln W50 | -0.0141 | 0.006090 | -0.07 | +1.15 | 0.126 | Fails |
| H2b | ln D5-75 | -0.0202 | 0.006089 | -0.05 | +0.77 | 0.219 | Fails |
| *Panel B. Registered regression, without ln VIX (reported alongside)* | | | | | | | |
| H2a | ln FAI_w | -0.0022 | 0.006107 | -0.19 | -0.94 | 0.826 | (fails) |
| H2b | ln W50 | -0.0164 | 0.006103 | -0.12 | +1.13 | 0.130 | (fails) |
| H2b | ln D5-75 | -0.0248 | 0.006100 | -0.08 | +0.94 | 0.175 | (fails) |

Notes: 2019-2025 (targets from 2019-01-02 to 2025-12-30), n = 1,743, with coefficients fixed on 2010-2018 (β shown). MSE: of the model with X; without X it is 0.006086 (Panel A) and 0.006095 (Panel B). R2_OS = 1 - MSE(with X) / MSE(without X), in percent. Clark-West: one-sided test that X improves the forecast, with a Newey-West standard error. A pass needs both CW p < 5% and R2_OS > 0 (D-034); the ln D5-75 row applies the robustness rule to H2b. Panel B verdicts in brackets: reported, not judged.

### Table A1. H2 in sample: leave one year out (appendix)

| Test | X | Full | 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | Kept |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H2a (i) | ln FAI_w | -2.30 | -2.05 | -2.14 | -2.33 | -2.17 | -2.26 | -2.16 | -2.32 | **-1.39** | -2.55 | 8 of 9 |
| H2a (ii) | ln FAI_w | -0.39 | -0.00 | **+0.16** | -0.47 | -1.06 | -0.32 | -0.35 | -0.75 | -0.12 | -0.09 | 0 of 9 |
| H2b | ln W50 | -2.39 | **-2.06** | -2.12 | -2.18 | -2.23 | -2.58 | -2.24 | -2.39 | -2.33 | -2.19 | 9 of 9 |
| H2b | ln D5-75 | -1.66 | -1.07 | -2.07 | -1.28 | -1.66 | -2.03 | -1.43 | -1.55 | **-1.04** | -1.94 | 2 of 9 |

Notes: t on X when one calendar year of 2010-2018 is left out (D-027 regression). Kept: refits significant at 5% with the full-sample sign. Bold: the year whose omission moves t furthest toward zero. Exploratory influence check named before the run (D-034 c); verdicts come from the full sample. H2a (ii) also includes ln FAI; the ln D5-75 row applies the robustness rule to H2b.

### Table A2. H2 with the return left unadjusted for dividends (appendix)

| Test | X | Dividend added back (main) | Unadjusted |
|---|---|---|---|
| H2a (i) | ln FAI_w | -0.0058 (-2.30) | -0.0058 (-2.30) |
| H2a (ii) | ln FAI_w | -0.0074 (-0.39) | -0.0066 (-0.34) |
| H2b | ln W50 | -0.0141 (-2.39) | -0.0141 (-2.39) |
| H2b | ln D5-75 | -0.0202 (-1.66) | -0.0203 (-1.66) |
| H2a out of sample | ln FAI_w | R2_OS -0.32%, CW p 0.403 | R2_OS -0.32%, CW p 0.399 |
| H2b out of sample | ln W50 | R2_OS -0.07%, CW p 0.126 | R2_OS -0.07%, CW p 0.127 |
| H2b out of sample | ln D5-75 | R2_OS -0.05%, CW p 0.219 | R2_OS -0.06%, CW p 0.224 |

Notes: r_d is SPY's close-to-close log return with the cash dividend added back on the 64 ex-dividend days of 2010-2025 (D-034 a); the right column leaves it unadjusted, on the same days. In sample: β (t). Reported alongside, not judged.

### Table A3. Secondary: next-day VIX jump logit (appendix)

| X | Coefficient shown | Coefficient | t | p | Converged |
|---|---|---|---|---|---|
| (none) | ln VIX | -2.007 | -2.51 | 0.012 | yes |
| ln FAI_w | ln FAI_w | +0.422 | +1.54 | 0.124 | yes |
| ln W50 | ln W50 | -0.308 | -1.30 | 0.192 | yes |

Notes: Logit for a next-day VIX jump, d ln VIX > ln 1.2, 2010-2018, n = 2,245 with 52 jump days, D-027 regressors, HAC sandwich standard errors. Secondary, reported but not a hypothesis (HYPOTHESES.md). The first row has no X and shows the coefficient on ln VIX.
