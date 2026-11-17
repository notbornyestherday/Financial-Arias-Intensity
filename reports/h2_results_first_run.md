# H2 results (registered tests, with D-027)

Written by `scripts/h2_tests.py`. How each outcome is read was fixed in advance in `paper/interpretation_table.md`.

## Primary: flagged prints removed

3,989 test days with every H2 variable (2,245 in 2010-2018, 1,744 in 2019-2025) of 3,989 test days; 64 ex-dividend days with the dividend added back.
Days dropped for a missing variable: none. SPY days without a VIX close: none. VIX dates that are not SPY sessions: 2010-11-26, 2011-11-25, 2012-07-03, 2012-11-23, 2012-12-24, 2013-07-03, 2013-11-29, 2013-12-24, 2014-07-03, 2014-11-28, 2014-12-24, 2015-11-27, 2015-12-24, 2016-11-25, 2017-07-03, 2017-11-24, 2018-07-03, 2018-11-23, 2018-12-24, 2019-07-03, 2019-11-29, 2019-12-24, 2020-11-27, 2020-12-24, 2021-04-12, 2021-11-26, 2022-05-30, 2022-06-20, 2022-07-04, 2022-09-05, 2022-11-24, 2022-11-25, 2023-01-16, 2023-02-20, 2023-05-29, 2023-06-19, 2023-07-03, 2023-07-04, 2023-09-04, 2023-11-23, 2023-11-24, 2024-01-15, 2024-02-19, 2024-05-27, 2024-06-19, 2024-07-03, 2024-07-04, 2024-09-02, 2024-11-28, 2024-11-29, 2024-12-24, 2025-01-09, 2025-01-20, 2025-02-17, 2025-05-26, 2025-06-19, 2025-07-03, 2025-07-04, 2025-09-01, 2025-11-27, 2025-11-28, 2025-12-24.

### Verdicts (D-027 regression, raw p at 5%)

- H2a (i): b != 0 (b < 0) (p 0.022).
- H2a (ii): not significant (p 0.698).
- H2b: b != 0 (b < 0), but fragile (D5-75 disagrees) (p 0.017). With D5-75: not significant.
- H2a out of sample: fails (p 0.366).
- H2b out of sample: fails (p 0.106). With D5-75: fails.

### Holm family (D-029)

| test | raw p | kind | Holm p | raw < 5% | Holm < 5% |
|---|---|---|---|---|---|
| H1b | 0.5832 | two-sided | 1.0000 | False | False |
| H1c concentration | 0.0000 | two-sided | 0.0000 | True | True |
| H2a (i) | 0.0216 | two-sided | 0.1081 | True | False |
| H2a (ii) | 0.6981 | two-sided | 1.0000 | False | False |
| H2b | 0.0169 | two-sided | 0.1013 | True | False |
| H2a out of sample | 0.3664 | one-sided (Clark-West) | 1.0000 | False | False |
| H2b out of sample | 0.1063 | one-sided (Clark-West) | 0.4254 | False | False |

### In sample, 2010-2018 (coefficient on X)

b x SD(X) is the change in next-day d ln VIX for a one-SD move in X.

| test | X | also in | spec | role | b | se | t | p | b x SD(X) | n | lag |
|---|---|---|---|---|---|---|---|---|---|---|---|
| H2a (i) | ln FAI_w |  | D-027 | primary | -0.0058 | 0.0025 | -2.30 | 0.022 | -0.0049 | 2245 | 7 |
| H2a (ii) | ln FAI_w | ln FAI | D-027 | primary | -0.0074 | 0.0191 | -0.39 | 0.698 | -0.0062 | 2245 | 7 |
| H2b | ln W50 |  | D-027 | primary | -0.0141 | 0.0059 | -2.39 | 0.017 | -0.0046 | 2245 | 7 |
| H2b | ln D5-75 |  | D-027 | robustness | -0.0202 | 0.0122 | -1.66 | 0.098 | -0.0030 | 2245 | 7 |
| H2a (i) | ln FAI_w (Corwin-Schultz) |  | D-027 | alongside (D-030) | -0.0056 | 0.0024 | -2.31 | 0.021 | -0.0051 | 2245 | 7 |
| H2a (ii) | ln FAI_w (Corwin-Schultz) | ln FAI | D-027 | alongside (D-030) | -0.0322 | 0.0346 | -0.93 | 0.352 | -0.0297 | 2245 | 7 |
| H2a (i) | ln FAI_c (floored 1/C) |  | D-027 | alongside (D-030) | -0.0040 | 0.0017 | -2.39 | 0.017 | -0.0044 | 2245 | 7 |
| H2a (ii) | ln FAI_c (floored 1/C) | ln FAI | D-027 | alongside (D-030) | -0.0020 | 0.0025 | -0.80 | 0.423 | -0.0022 | 2245 | 7 |
| H2a (i) | ln FAI_w |  | registered | primary | -0.0022 | 0.0023 | -0.94 | 0.347 | -0.0019 | 2245 | 7 |
| H2a (ii) | ln FAI_w | ln FAI | registered | primary | -0.0107 | 0.0190 | -0.57 | 0.572 | -0.0090 | 2245 | 7 |
| H2b | ln W50 |  | registered | primary | -0.0164 | 0.0056 | -2.96 | 0.003 | -0.0054 | 2245 | 7 |
| H2b | ln D5-75 |  | registered | robustness | -0.0248 | 0.0116 | -2.14 | 0.032 | -0.0037 | 2245 | 7 |
| H2a (i) | ln FAI_w (Corwin-Schultz) |  | registered | alongside (D-030) | -0.0020 | 0.0022 | -0.89 | 0.373 | -0.0018 | 2245 | 7 |
| H2a (ii) | ln FAI_w (Corwin-Schultz) | ln FAI | registered | alongside (D-030) | -0.0096 | 0.0334 | -0.29 | 0.773 | -0.0089 | 2245 | 7 |
| H2a (i) | ln FAI_c (floored 1/C) |  | registered | alongside (D-030) | -0.0023 | 0.0016 | -1.41 | 0.158 | -0.0025 | 2245 | 7 |
| H2a (ii) | ln FAI_c (floored 1/C) | ln FAI | registered | alongside (D-030) | -0.0024 | 0.0025 | -0.95 | 0.342 | -0.0026 | 2245 | 7 |

Full D-027 regression for H2a (i):

| regressor | coef | se | t |
|---|---|---|---|
| ln FAI_w | -0.0058 | 0.0025 | -2.30 |
| ln RV | +0.0041 | 0.0046 | +0.90 |
| r | -0.0128 | 0.3669 | -0.03 |
| min(r, 0) | +0.1217 | 0.7076 | +0.17 |
| d ln VIX | -0.0241 | 0.0460 | -0.52 |
| ln VIX | -0.0381 | 0.0115 | -3.30 |

### Out of sample, 2019-2025 (coefficients fixed on 2010-2018)

R2_OS = 1 - MSE(with X) / MSE(without X). Clark-West p is one-sided.

| test | X | spec | role | b (2010-2018) | MSE without | MSE with | R2_OS | CW t | CW p | n |
|---|---|---|---|---|---|---|---|---|---|---|
| H2a out of sample | ln FAI_w | D-027 | primary | -0.0058 | 0.005983 | 0.006001 | -0.0030 | +0.34 | 0.366 | 1744 |
| H2b out of sample | ln W50 | D-027 | primary | -0.0141 | 0.005983 | 0.005985 | -0.0004 | +1.25 | 0.106 | 1744 |
| H2b out of sample | ln D5-75 | D-027 | robustness | -0.0202 | 0.005983 | 0.005986 | -0.0005 | +0.78 | 0.217 | 1744 |
| H2a out of sample | ln FAI_w | registered | primary | -0.0022 | 0.005989 | 0.006000 | -0.0018 | -0.78 | 0.781 | 1744 |
| H2b out of sample | ln W50 | registered | primary | -0.0164 | 0.005989 | 0.005996 | -0.0011 | +1.17 | 0.122 | 1744 |
| H2b out of sample | ln D5-75 | registered | robustness | -0.0248 | 0.005989 | 0.005994 | -0.0009 | +0.91 | 0.182 | 1744 |

### Leave one year out (exploratory influence check, D-034)

Each in-sample test refitted nine times, leaving out one year of 2010-2018. The verdicts above come from the full sample; this shows how much a result rests on one stretch of history. "Kept" counts refits significant at 5% with the full-sample sign.

| test | X | t (full) | b range | t range | kept | most influential year | t without it |
|---|---|---|---|---|---|---|---|
| H2a (i) | ln FAI_w | -2.30 | -0.0074 to -0.0037 | -2.55 to -1.39 | 8 of 9 | 2017 | -1.39 |
| H2a (ii) | ln FAI_w | -0.39 | -0.0210 to +0.0031 | -1.06 to +0.16 | 0 of 9 | 2011 | +0.16 |
| H2b | ln W50 | -2.39 | -0.0164 to -0.0112 | -2.58 to -2.06 | 9 of 9 | 2010 | -2.06 |
| H2b | ln D5-75 | -1.66 | -0.0264 to -0.0124 | -2.07 to -1.04 | 2 of 9 | 2017 | -1.04 |

### Dividends not added back (reported alongside, D-034)

The main tests with r_d as the unadjusted prices give it on ex-dividend days, same days, D-027 regression. Not judged; it shows what the adjustment changes.

| test | X | b (main) | t (main) | b (unadjusted) | t (unadjusted) |
|---|---|---|---|---|---|
| H2a (i) | ln FAI_w | -0.0058 | -2.30 | -0.0058 | -2.30 |
| H2a (ii) | ln FAI_w | -0.0074 | -0.39 | -0.0066 | -0.34 |
| H2b | ln W50 | -0.0141 | -2.39 | -0.0141 | -2.39 |
| H2b | ln D5-75 | -0.0202 | -1.66 | -0.0203 | -1.66 |
| H2a out of sample | ln FAI_w | R2_OS -0.0030 | CW p 0.366 | R2_OS -0.0029 | CW p 0.362 |
| H2b out of sample | ln W50 | R2_OS -0.0004 | CW p 0.106 | R2_OS -0.0004 | CW p 0.108 |
| H2b out of sample | ln D5-75 | R2_OS -0.0005 | CW p 0.217 | R2_OS -0.0006 | CW p 0.221 |

### Secondary: next-day VIX jump logit (d ln VIX > ln 1.2), 2010-2018

52 jump days in sample. D-027 regressors.

| X | coefficient shown | coef | se | t | p | n | events | converged |
|---|---|---|---|---|---|---|---|---|
| (none) | ln VIX | -2.007 | 0.800 | -2.51 | 0.012 | 2245 | 52 | True |
| ln FAI_w | ln FAI_w | +0.422 | 0.275 | +1.54 | 0.124 | 2245 | 52 | True |
| ln W50 | ln W50 | -0.308 | 0.236 | -1.30 | 0.192 | 2245 | 52 | True |

## Flagged prints kept

3,989 test days with every H2 variable (2,245 in 2010-2018, 1,744 in 2019-2025) of 3,989 test days; 64 ex-dividend days with the dividend added back.
Days dropped for a missing variable: none. SPY days without a VIX close: none. VIX dates that are not SPY sessions: 2010-11-26, 2011-11-25, 2012-07-03, 2012-11-23, 2012-12-24, 2013-07-03, 2013-11-29, 2013-12-24, 2014-07-03, 2014-11-28, 2014-12-24, 2015-11-27, 2015-12-24, 2016-11-25, 2017-07-03, 2017-11-24, 2018-07-03, 2018-11-23, 2018-12-24, 2019-07-03, 2019-11-29, 2019-12-24, 2020-11-27, 2020-12-24, 2021-04-12, 2021-11-26, 2022-05-30, 2022-06-20, 2022-07-04, 2022-09-05, 2022-11-24, 2022-11-25, 2023-01-16, 2023-02-20, 2023-05-29, 2023-06-19, 2023-07-03, 2023-07-04, 2023-09-04, 2023-11-23, 2023-11-24, 2024-01-15, 2024-02-19, 2024-05-27, 2024-06-19, 2024-07-03, 2024-07-04, 2024-09-02, 2024-11-28, 2024-11-29, 2024-12-24, 2025-01-09, 2025-01-20, 2025-02-17, 2025-05-26, 2025-06-19, 2025-07-03, 2025-07-04, 2025-09-01, 2025-11-27, 2025-11-28, 2025-12-24.

### Verdicts (D-027 regression, raw p at 5%)

- H2a (i): b != 0 (b < 0) (p 0.022).
- H2a (ii): not significant (p 0.698).
- H2b: b != 0 (b < 0), but fragile (D5-75 disagrees) (p 0.017). With D5-75: not significant.
- H2a out of sample: fails (p 0.367).
- H2b out of sample: fails (p 0.106). With D5-75: fails.

### In sample, 2010-2018 (coefficient on X)

b x SD(X) is the change in next-day d ln VIX for a one-SD move in X.

| test | X | also in | spec | role | b | se | t | p | b x SD(X) | n | lag |
|---|---|---|---|---|---|---|---|---|---|---|---|
| H2a (i) | ln FAI_w |  | D-027 | primary | -0.0058 | 0.0025 | -2.30 | 0.022 | -0.0049 | 2245 | 7 |
| H2a (ii) | ln FAI_w | ln FAI | D-027 | primary | -0.0074 | 0.0191 | -0.39 | 0.698 | -0.0062 | 2245 | 7 |
| H2b | ln W50 |  | D-027 | primary | -0.0141 | 0.0059 | -2.39 | 0.017 | -0.0046 | 2245 | 7 |
| H2b | ln D5-75 |  | D-027 | robustness | -0.0202 | 0.0122 | -1.65 | 0.098 | -0.0030 | 2245 | 7 |
| H2a (i) | ln FAI_w (Corwin-Schultz) |  | D-027 | alongside (D-030) | -0.0056 | 0.0024 | -2.31 | 0.021 | -0.0051 | 2245 | 7 |
| H2a (ii) | ln FAI_w (Corwin-Schultz) | ln FAI | D-027 | alongside (D-030) | -0.0322 | 0.0346 | -0.93 | 0.352 | -0.0296 | 2245 | 7 |
| H2a (i) | ln FAI_c (floored 1/C) |  | D-027 | alongside (D-030) | -0.0040 | 0.0017 | -2.39 | 0.017 | -0.0044 | 2245 | 7 |
| H2a (ii) | ln FAI_c (floored 1/C) | ln FAI | D-027 | alongside (D-030) | -0.0020 | 0.0025 | -0.80 | 0.424 | -0.0022 | 2245 | 7 |
| H2a (i) | ln FAI_w |  | registered | primary | -0.0022 | 0.0023 | -0.94 | 0.347 | -0.0019 | 2245 | 7 |
| H2a (ii) | ln FAI_w | ln FAI | registered | primary | -0.0107 | 0.0190 | -0.57 | 0.572 | -0.0090 | 2245 | 7 |
| H2b | ln W50 |  | registered | primary | -0.0165 | 0.0056 | -2.96 | 0.003 | -0.0054 | 2245 | 7 |
| H2b | ln D5-75 |  | registered | robustness | -0.0248 | 0.0116 | -2.14 | 0.032 | -0.0037 | 2245 | 7 |
| H2a (i) | ln FAI_w (Corwin-Schultz) |  | registered | alongside (D-030) | -0.0020 | 0.0022 | -0.89 | 0.373 | -0.0018 | 2245 | 7 |
| H2a (ii) | ln FAI_w (Corwin-Schultz) | ln FAI | registered | alongside (D-030) | -0.0097 | 0.0334 | -0.29 | 0.773 | -0.0089 | 2245 | 7 |
| H2a (i) | ln FAI_c (floored 1/C) |  | registered | alongside (D-030) | -0.0023 | 0.0016 | -1.41 | 0.158 | -0.0025 | 2245 | 7 |
| H2a (ii) | ln FAI_c (floored 1/C) | ln FAI | registered | alongside (D-030) | -0.0024 | 0.0025 | -0.95 | 0.343 | -0.0026 | 2245 | 7 |

Full D-027 regression for H2a (i):

| regressor | coef | se | t |
|---|---|---|---|
| ln FAI_w | -0.0058 | 0.0025 | -2.30 |
| ln RV | +0.0041 | 0.0046 | +0.90 |
| r | -0.0128 | 0.3669 | -0.03 |
| min(r, 0) | +0.1216 | 0.7076 | +0.17 |
| d ln VIX | -0.0241 | 0.0460 | -0.52 |
| ln VIX | -0.0381 | 0.0115 | -3.30 |

### Out of sample, 2019-2025 (coefficients fixed on 2010-2018)

R2_OS = 1 - MSE(with X) / MSE(without X). Clark-West p is one-sided.

| test | X | spec | role | b (2010-2018) | MSE without | MSE with | R2_OS | CW t | CW p | n |
|---|---|---|---|---|---|---|---|---|---|---|
| H2a out of sample | ln FAI_w | D-027 | primary | -0.0058 | 0.005983 | 0.006001 | -0.0030 | +0.34 | 0.367 | 1744 |
| H2b out of sample | ln W50 | D-027 | primary | -0.0141 | 0.005983 | 0.005985 | -0.0004 | +1.25 | 0.106 | 1744 |
| H2b out of sample | ln D5-75 | D-027 | robustness | -0.0202 | 0.005983 | 0.005986 | -0.0005 | +0.78 | 0.217 | 1744 |
| H2a out of sample | ln FAI_w | registered | primary | -0.0022 | 0.005989 | 0.006000 | -0.0018 | -0.78 | 0.781 | 1744 |
| H2b out of sample | ln W50 | registered | primary | -0.0165 | 0.005989 | 0.005996 | -0.0011 | +1.17 | 0.122 | 1744 |
| H2b out of sample | ln D5-75 | registered | robustness | -0.0248 | 0.005989 | 0.005994 | -0.0009 | +0.91 | 0.182 | 1744 |

### Leave one year out (exploratory influence check, D-034)

Each in-sample test refitted nine times, leaving out one year of 2010-2018. The verdicts above come from the full sample; this shows how much a result rests on one stretch of history. "Kept" counts refits significant at 5% with the full-sample sign.

| test | X | t (full) | b range | t range | kept | most influential year | t without it |
|---|---|---|---|---|---|---|---|
| H2a (i) | ln FAI_w | -2.30 | -0.0074 to -0.0037 | -2.55 to -1.39 | 8 of 9 | 2017 | -1.39 |
| H2a (ii) | ln FAI_w | -0.39 | -0.0210 to +0.0031 | -1.06 to +0.16 | 0 of 9 | 2011 | +0.16 |
| H2b | ln W50 | -2.39 | -0.0164 to -0.0112 | -2.58 to -2.06 | 9 of 9 | 2010 | -2.06 |
| H2b | ln D5-75 | -1.65 | -0.0263 to -0.0124 | -2.07 to -1.04 | 2 of 9 | 2017 | -1.04 |

### Dividends not added back (reported alongside, D-034)

The main tests with r_d as the unadjusted prices give it on ex-dividend days, same days, D-027 regression. Not judged; it shows what the adjustment changes.

| test | X | b (main) | t (main) | b (unadjusted) | t (unadjusted) |
|---|---|---|---|---|---|
| H2a (i) | ln FAI_w | -0.0058 | -2.30 | -0.0058 | -2.30 |
| H2a (ii) | ln FAI_w | -0.0074 | -0.39 | -0.0066 | -0.34 |
| H2b | ln W50 | -0.0141 | -2.39 | -0.0141 | -2.39 |
| H2b | ln D5-75 | -0.0202 | -1.65 | -0.0203 | -1.66 |
| H2a out of sample | ln FAI_w | R2_OS -0.0030 | CW p 0.367 | R2_OS -0.0029 | CW p 0.362 |
| H2b out of sample | ln W50 | R2_OS -0.0004 | CW p 0.106 | R2_OS -0.0004 | CW p 0.108 |
| H2b out of sample | ln D5-75 | R2_OS -0.0005 | CW p 0.217 | R2_OS -0.0006 | CW p 0.221 |

### Secondary: next-day VIX jump logit (d ln VIX > ln 1.2), 2010-2018

52 jump days in sample. D-027 regressors.

| X | coefficient shown | coef | se | t | p | n | events | converged |
|---|---|---|---|---|---|---|---|---|
| (none) | ln VIX | -2.007 | 0.800 | -2.51 | 0.012 | 2245 | 52 | True |
| ln FAI_w | ln FAI_w | +0.422 | 0.275 | +1.54 | 0.124 | 2245 | 52 | True |
| ln W50 | ln W50 | -0.308 | 0.236 | -1.30 | 0.192 | 2245 | 52 | True |
