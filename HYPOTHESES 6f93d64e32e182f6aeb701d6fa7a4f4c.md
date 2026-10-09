# HYPOTHESES

## Question

Does *how* intraday volatility is delivered (one burst vs. a slow grind) carry information
that total volatility doesn’t?

## Benchmark

Daily realized variance, RV = sum of squared 1-minute regular-hours log returns. A measure
“adds information” only if it improves on RV in the tests below. A negative result will be
reported as such.

## Sample and conventions

- SPY 1-minute bars, regular hours, 2009-01 to 2025-12. 2009 is warm-up for trailing
windows. In-sample 2010-2018; out-of-sample 2019-2025 with coefficients fixed in-sample.
- Signal: deseasonalized returns r̃ (trailing 60-day per-minute RMS, prior days only).
- Half-days are excluded from all tests. Halt days are kept; returns spanning a halt are
deseasonalized by the summed seasonal variance of the minutes they span.
- “RV decile” = decile of RV over the full sample.
- FOMC days = days with an FOMC statement released during regular hours (`ref/fomc_dates.csv`).
- Newey-West standard errors with lag floor(4(T/100)^(2/9)). Two-sided tests at 5%. All
tests are reported, with Holm-adjusted p-values alongside raw ones.

## Concentration measures

All three measures are read off the Husid curve H(t): the day’s cumulative Arias intensity
divided by its total, rising from 0 at the open to 1 at the close (Husid 1969; Arias 1970).
Each measures how long the curve takes to climb a set amount.

- **Primary: W50**, the shortest time in which H climbs 50 percentage points, wherever in
the day that happens.
- **Secondary, the seismology standard: D5-75**, the time H takes to climb from 5% to 75%,
the strong-phase significant duration (Bommer et al. 2009).
- **Reported for comparison: D5-95** (Trifunac and Brady 1975).

Why W50’s start point floats: an earthquake record starts and ends near quiet, so the 5%
point falls where strong shaking begins. A trading day doesn’t have a quiet stretch before the
event: ordinary trading adds energy at a steady rate all day, so a start fixed at 5% falls
in that background. W50 uses the same Husid curve but lets the start move to wherever the
climb is fastest.

Simulation, two days with identical RV, a 15-minute burst vs. a uniform grind. Separation d
(difference in means over pooled SD; higher is better), 1000 replications
(`scripts/sim_duration_power.py`, DECISIONS.md D-009):

| Burst | D5-95 | D5-75 | W50 |
| --- | --- | --- | --- |
| 12x, normal noise | 4.1 | 6.4 | 24.9 |
| 6x, normal noise | 3.0 | 6.4 | 9.9 |
| 4x, normal noise | 2.0 | 3.3 | 3.7 |
| 6x, fat-tailed noise, t(4) | 1.7 | 3.0 | 4.5 |

**Robustness rule:** Every test that uses W50 (H1a, H1b, H1c, H2b) is repeated with D5-75
in its place. If a W50 result reverses sign or loses significance with D5-75, the paper
reports it as fragile.

## H1: concentration separates liquidity breakdowns from information-driven moves

**H1a (named events; illustrative, n is tiny):** Let q(d) be the percentile of W50 on day
d among days in the same RV decile. Predictions: q < 10 on 2010-05-06 and on 2015-08-24;
median q > 50 across 2020-03-09, 03-12, 03-16 and 03-18. Falsified if any part fails. Because three of the four 2020 halts came within minutes of the open, H1a for the 2020 days is also reported with the first 30 minutes of each day excluded; the main prediction uses the full day.

**H1b (full sample, primary test):** Liquidity-driven price moves are transient;
information-driven moves are not. Concentrated days should therefore show more intraday
reversal. Reversal is measured by the variance ratio VR(30/5) of deseasonalized returns
(built from 5-minute blocks so 1-minute bid-ask bounce mostly cancels).
Regression: VR_d = a + b ln W50_d + RV-decile fixed effects + e, excluding FOMC days and
half-days, with flagged bad prints removed. Prediction: b > 0 (shorter window, more reversal).
Under independent increments E[VR] = 1 regardless of concentration. A preliminary
simulation with no reversal (16,000 days, normal and t(4) noise) gave slopes
indistinguishable from zero for W50, D5-75 and D5-95 (`scripts/sim_h1b_null.py`,
DECISIONS.md D-011). **Before running this on data, repeat that check on the full
pipeline: bid-ask bounce, estimated seasonality.** Bad prints bias toward the predicted
sign, which is why flagged prints are removed; results with them are reported too.

**H1c (positive control):** FOMC days concentrate energy by design, through information
rather than liquidity. Predictions: in ln W50_d = a + c FOMC_d + RV-decile FE + e, c < 0;
in the H1b regression with FOMC days included and an FOMC dummy added, the dummy is not
significantly negative. If FOMC days are not more concentrated, W50 is not measuring
concentration and H1b cannot be interpreted.

## H2: next-day VIX changes

Regression: d ln VIX_{d+1} = α + β X_d + γ1 ln RV_d + γ2 r_d + γ3 min(r_d, 0) + γ4 d ln VIX_d + ε,
where r_d is the SPY close-to-close log return. VIX closes after SPY, so all regressors are
known before the predicted window opens.

- **H2a (liquidity weighting):** X = ln FAI_w. (i) β ≠ 0 in-sample. (ii) β ≠ 0 with ln FAI
(unweighted) also included, which isolates the weighting from the deseasonalizing and
normalizing that FAI_w shares with FAI.
- **H2b (concentration):** X = ln W50. β ≠ 0 in-sample. Direction not predicted.
- **Out-of-sample:** for each of H2a and H2b: the model with X has lower 2019-2025 MSE than
the model without it, by a Clark-West test at 5%.
- Secondary, reported but not a hypothesis: logit for a next-day VIX jump,
d ln VIX_{d+1} > ln 1.2, with the same regressors.

## H3: differenced signal

Replacing r̃_t with r̃*t − r̃*{t−1} improves neither H1b nor H2. Expected, because
differencing amplifies bid-ask noise. Reported as a check, not a finding.

## Exploratory (not confirmatory)

Whether W50 predicts next-day and next-week RV beyond HAR-RV terms (Corsi 2009);
next-day close-to-close reversal on concentrated days; 1-minute vs. 5-minute bars; QQQ;
median-based seasonality; event-detection windows.

## What a negative result looks like

If b in H1b is indistinguishable from zero and H2a and H2b fail out of sample, the paper
reports that, in SPY at 1-minute resolution, the timing of volatility within the day carries
no information beyond RV.