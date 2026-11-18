# Robustness results (exploratory; D-018, H3, D-025 a)

Written by `scripts/robustness.py`. Nothing here changes a registered verdict or enters the Holm family. How each outcome is read was fixed in advance in `paper/interpretation_table.md` (robustness rows, D-036).

## Primary: flagged prints removed

H1 sample: 3,989 test days (3,859 without FOMC days). H2 sample: 2,245 days in 2010-2018, 1,743 in 2019-2025, the same days as the registered H2 run.

### 1. D-018 benchmark comparison (exploratory)

(a) ln W50 with each benchmark as a control, and all three; (b) each benchmark in place of ln W50. H1b: VR** with RV-decile fixed effects, FOMC days out. H2b: next-day d ln VIX with the D-027 controls, 2010-2018.

| test | specification | regressor | b | se | t | p | n |
|---|---|---|---|---|---|---|---|
| H1b | W50 alone (registered) | ln W50 | -0.0083 | 0.0151 | -0.55 | 0.583 | 3859 |
| H1b | (a) W50 + jump share | ln W50 | -0.0095 | 0.0151 | -0.63 | 0.526 | 3859 |
| H1b | (a) W50 + jump share | jump share | -0.1098 | 0.0750 | -1.47 | 0.143 | 3859 |
| H1b | (a) W50 + ln RQ ratio | ln W50 | -0.0215 | 0.0181 | -1.19 | 0.234 | 3859 |
| H1b | (a) W50 + ln RQ ratio | ln RQ ratio | -0.0165 | 0.0126 | -1.31 | 0.191 | 3859 |
| H1b | (a) W50 + downside share | ln W50 | -0.0114 | 0.0150 | -0.76 | 0.447 | 3859 |
| H1b | (a) W50 + downside share | downside share | -0.1730 | 0.0727 | -2.38 | 0.017 | 3859 |
| H1b | (a) W50 + all three | ln W50 | -0.0182 | 0.0184 | -0.99 | 0.322 | 3859 |
| H1b | (a) W50 + all three | jump share | -0.0980 | 0.0829 | -1.18 | 0.237 | 3859 |
| H1b | (a) W50 + all three | ln RQ ratio | -0.0069 | 0.0140 | -0.49 | 0.621 | 3859 |
| H1b | (a) W50 + all three | downside share | -0.1768 | 0.0732 | -2.42 | 0.016 | 3859 |
| H1b | (b) jump share in place of W50 | jump share | -0.1061 | 0.0749 | -1.42 | 0.156 | 3859 |
| H1b | (b) ln RQ ratio in place of W50 | ln RQ ratio | -0.0062 | 0.0107 | -0.58 | 0.561 | 3859 |
| H1b | (b) downside share in place of W50 | downside share | -0.1677 | 0.0720 | -2.33 | 0.020 | 3859 |
| H2b | W50 alone (registered) | ln W50 | -0.0141 | 0.0059 | -2.39 | 0.017 | 2245 |
| H2b | (a) W50 + jump share | ln W50 | -0.0141 | 0.0059 | -2.39 | 0.017 | 2245 |
| H2b | (a) W50 + jump share | jump share | -0.0010 | 0.0321 | -0.03 | 0.975 | 2245 |
| H2b | (a) W50 + ln RQ ratio | ln W50 | -0.0236 | 0.0077 | -3.08 | 0.002 | 2245 |
| H2b | (a) W50 + ln RQ ratio | ln RQ ratio | -0.0123 | 0.0062 | -1.98 | 0.047 | 2245 |
| H2b | (a) W50 + downside share | ln W50 | -0.0141 | 0.0059 | -2.38 | 0.017 | 2245 |
| H2b | (a) W50 + downside share | downside share | -0.0148 | 0.0353 | -0.42 | 0.676 | 2245 |
| H2b | (a) W50 + all three | ln W50 | -0.0260 | 0.0082 | -3.17 | 0.002 | 2245 |
| H2b | (a) W50 + all three | jump share | +0.0439 | 0.0365 | +1.20 | 0.229 | 2245 |
| H2b | (a) W50 + all three | ln RQ ratio | -0.0165 | 0.0070 | -2.35 | 0.019 | 2245 |
| H2b | (a) W50 + all three | downside share | -0.0092 | 0.0356 | -0.26 | 0.797 | 2245 |
| H2b | (b) jump share in place of W50 | jump share | +0.0087 | 0.0311 | +0.28 | 0.780 | 2245 |
| H2b | (b) ln RQ ratio in place of W50 | ln RQ ratio | +0.0009 | 0.0048 | +0.18 | 0.856 | 2245 |
| H2b | (b) downside share in place of W50 | downside share | -0.0134 | 0.0345 | -0.39 | 0.697 | 2245 |

(c) Out of sample, 2019-2025 (coefficients fixed on 2010-2018; pass = Clark-West p < 5% and R2_OS > 0, as D-034).

| X | b (2010-2018) | R2_OS | CW t | CW p | passes | n |
|---|---|---|---|---|---|---|
| ln W50 | -0.0141 | -0.0007 | +1.15 | 0.126 | False | 1743 |
| jump share | +0.0087 | -0.0007 | -2.61 | 0.995 | False | 1743 |
| ln RQ ratio | +0.0009 | -0.0002 | -0.71 | 0.761 | False | 1743 |
| downside share | -0.0134 | -0.0006 | -0.79 | 0.786 | False | 1743 |

### 2. H3: differenced signal (registered check)

Each test with r~ and with a_t = r~_t - r~_{t-1}. Pass = the registered rule (raw p at 5%, b > 0 for H1b; out of sample, CW p < 5% and R2_OS > 0). Improves = passes with the differenced signal where r~ fails; Holm over the six main comparisons (D-036); the D5-75 versions are shown, not judged.

| test | r~ | pass | differenced | pass | p (diff) | Holm p | improves |
|---|---|---|---|---|---|---|---|
| H1b | -0.0083 (t -0.55) | False | -0.0129 (t -0.89) | False | 0.374 | 1.000 | no |
| H1b, D5-75 | +0.0289 (t +1.01) | False | +0.0207 (t +0.73) | False | 0.465 |  | not judged |
| H2a (i) | -0.0058 (t -2.30) | True | -0.0058 (t -2.29) | True | 0.022 | 0.131 | no |
| H2a (ii) | -0.0074 (t -0.39) | False | -0.0067 (t -0.36) | False | 0.720 | 1.000 | no |
| H2b | -0.0141 (t -2.39) | True | -0.0117 (t -2.11) | True | 0.035 | 0.173 | no |
| H2b, D5-75 | -0.0202 (t -1.66) | False | -0.0242 (t -1.98) | True | 0.047 |  | not judged |
| H2a out of sample | R2_OS -0.0032 (CW p 0.403) | False | R2_OS -0.0036 (CW p 0.454) | False | 0.454 | 1.000 | no |
| H2b out of sample | R2_OS -0.0007 (CW p 0.126) | False | R2_OS +0.0015 (CW p 0.036) | True | 0.036 | 0.173 | before Holm only |
| H2b out of sample, D5-75 | R2_OS -0.0005 (CW p 0.219) | False | R2_OS -0.0008 (CW p 0.182) | False | 0.182 |  | not judged |

H3 improves before Holm only: H2b out of sample passes on its raw p with the differenced signal but not after Holm over the six comparisons, which is within what chance would produce.

### 3. H1b without Fed Chair appearances (D-025 a, exploratory)

78 Fed Chair days listed for 2010-2025; 78 are H1 test days, of which 1 are also FOMC days (already out).

| test | specification | regressor | b | se | t | p | n |
|---|---|---|---|---|---|---|---|
| H1b | registered (FOMC days out) | ln W50 | -0.0083 | 0.0151 | -0.55 | 0.583 | 3859 |
| H1b | FOMC and Fed Chair days out (D-025 a) | ln W50 | -0.0038 | 0.0153 | -0.25 | 0.803 | 3782 |
| H1b | registered (FOMC days out) | ln D5-75 | +0.0289 | 0.0287 | +1.01 | 0.314 | 3859 |
| H1b | FOMC and Fed Chair days out (D-025 a) | ln D5-75 | +0.0311 | 0.0297 | +1.05 | 0.295 | 3782 |

## Flagged prints kept

H1 sample: 3,989 test days (3,859 without FOMC days). H2 sample: 2,245 days in 2010-2018, 1,743 in 2019-2025, the same days as the registered H2 run.

### 1. D-018 benchmark comparison (exploratory)

(a) ln W50 with each benchmark as a control, and all three; (b) each benchmark in place of ln W50. H1b: VR** with RV-decile fixed effects, FOMC days out. H2b: next-day d ln VIX with the D-027 controls, 2010-2018.

| test | specification | regressor | b | se | t | p | n |
|---|---|---|---|---|---|---|---|
| H1b | W50 alone (registered) | ln W50 | -0.0083 | 0.0151 | -0.55 | 0.580 | 3859 |
| H1b | (a) W50 + jump share | ln W50 | -0.0096 | 0.0151 | -0.64 | 0.523 | 3859 |
| H1b | (a) W50 + jump share | jump share | -0.1090 | 0.0750 | -1.45 | 0.146 | 3859 |
| H1b | (a) W50 + ln RQ ratio | ln W50 | -0.0215 | 0.0181 | -1.19 | 0.235 | 3859 |
| H1b | (a) W50 + ln RQ ratio | ln RQ ratio | -0.0163 | 0.0126 | -1.29 | 0.196 | 3859 |
| H1b | (a) W50 + downside share | ln W50 | -0.0115 | 0.0150 | -0.77 | 0.444 | 3859 |
| H1b | (a) W50 + downside share | downside share | -0.1725 | 0.0726 | -2.38 | 0.018 | 3859 |
| H1b | (a) W50 + all three | ln W50 | -0.0181 | 0.0184 | -0.99 | 0.323 | 3859 |
| H1b | (a) W50 + all three | jump share | -0.0976 | 0.0829 | -1.18 | 0.239 | 3859 |
| H1b | (a) W50 + all three | ln RQ ratio | -0.0068 | 0.0140 | -0.48 | 0.628 | 3859 |
| H1b | (a) W50 + all three | downside share | -0.1763 | 0.0731 | -2.41 | 0.016 | 3859 |
| H1b | (b) jump share in place of W50 | jump share | -0.1053 | 0.0749 | -1.41 | 0.160 | 3859 |
| H1b | (b) ln RQ ratio in place of W50 | ln RQ ratio | -0.0061 | 0.0107 | -0.57 | 0.570 | 3859 |
| H1b | (b) downside share in place of W50 | downside share | -0.1672 | 0.0720 | -2.32 | 0.020 | 3859 |
| H2b | W50 alone (registered) | ln W50 | -0.0141 | 0.0059 | -2.39 | 0.017 | 2245 |
| H2b | (a) W50 + jump share | ln W50 | -0.0141 | 0.0059 | -2.39 | 0.017 | 2245 |
| H2b | (a) W50 + jump share | jump share | -0.0010 | 0.0321 | -0.03 | 0.975 | 2245 |
| H2b | (a) W50 + ln RQ ratio | ln W50 | -0.0236 | 0.0077 | -3.08 | 0.002 | 2245 |
| H2b | (a) W50 + ln RQ ratio | ln RQ ratio | -0.0123 | 0.0062 | -1.98 | 0.047 | 2245 |
| H2b | (a) W50 + downside share | ln W50 | -0.0142 | 0.0059 | -2.38 | 0.017 | 2245 |
| H2b | (a) W50 + downside share | downside share | -0.0148 | 0.0353 | -0.42 | 0.675 | 2245 |
| H2b | (a) W50 + all three | ln W50 | -0.0260 | 0.0082 | -3.17 | 0.002 | 2245 |
| H2b | (a) W50 + all three | jump share | +0.0439 | 0.0365 | +1.20 | 0.229 | 2245 |
| H2b | (a) W50 + all three | ln RQ ratio | -0.0165 | 0.0070 | -2.35 | 0.019 | 2245 |
| H2b | (a) W50 + all three | downside share | -0.0092 | 0.0356 | -0.26 | 0.797 | 2245 |
| H2b | (b) jump share in place of W50 | jump share | +0.0087 | 0.0311 | +0.28 | 0.779 | 2245 |
| H2b | (b) ln RQ ratio in place of W50 | ln RQ ratio | +0.0009 | 0.0048 | +0.18 | 0.856 | 2245 |
| H2b | (b) downside share in place of W50 | downside share | -0.0135 | 0.0345 | -0.39 | 0.696 | 2245 |

(c) Out of sample, 2019-2025 (coefficients fixed on 2010-2018; pass = Clark-West p < 5% and R2_OS > 0, as D-034).

| X | b (2010-2018) | R2_OS | CW t | CW p | passes | n |
|---|---|---|---|---|---|---|
| ln W50 | -0.0141 | -0.0007 | +1.14 | 0.126 | False | 1743 |
| jump share | +0.0087 | -0.0007 | -2.61 | 0.995 | False | 1743 |
| ln RQ ratio | +0.0009 | -0.0002 | -0.71 | 0.761 | False | 1743 |
| downside share | -0.0135 | -0.0006 | -0.79 | 0.786 | False | 1743 |

### 2. H3: differenced signal (registered check)

Each test with r~ and with a_t = r~_t - r~_{t-1}. Pass = the registered rule (raw p at 5%, b > 0 for H1b; out of sample, CW p < 5% and R2_OS > 0). Improves = passes with the differenced signal where r~ fails; Holm over the six main comparisons (D-036); the D5-75 versions are shown, not judged.

| test | r~ | pass | differenced | pass | p (diff) | Holm p | improves |
|---|---|---|---|---|---|---|---|
| H1b | -0.0083 (t -0.55) | False | -0.0130 (t -0.90) | False | 0.369 | 1.000 | no |
| H1b, D5-75 | +0.0287 (t +1.00) | False | +0.0205 (t +0.72) | False | 0.469 |  | not judged |
| H2a (i) | -0.0058 (t -2.30) | True | -0.0058 (t -2.29) | True | 0.022 | 0.131 | no |
| H2a (ii) | -0.0074 (t -0.39) | False | -0.0067 (t -0.36) | False | 0.721 | 1.000 | no |
| H2b | -0.0141 (t -2.39) | True | -0.0118 (t -2.12) | True | 0.034 | 0.171 | no |
| H2b, D5-75 | -0.0202 (t -1.65) | False | -0.0242 (t -1.98) | True | 0.047 |  | not judged |
| H2a out of sample | R2_OS -0.0032 (CW p 0.403) | False | R2_OS -0.0036 (CW p 0.454) | False | 0.454 | 1.000 | no |
| H2b out of sample | R2_OS -0.0007 (CW p 0.126) | False | R2_OS +0.0015 (CW p 0.036) | True | 0.036 | 0.171 | before Holm only |
| H2b out of sample, D5-75 | R2_OS -0.0005 (CW p 0.219) | False | R2_OS -0.0008 (CW p 0.182) | False | 0.182 |  | not judged |

H3 improves before Holm only: H2b out of sample passes on its raw p with the differenced signal but not after Holm over the six comparisons, which is within what chance would produce.

### 3. H1b without Fed Chair appearances (D-025 a, exploratory)

78 Fed Chair days listed for 2010-2025; 78 are H1 test days, of which 1 are also FOMC days (already out).

| test | specification | regressor | b | se | t | p | n |
|---|---|---|---|---|---|---|---|
| H1b | registered (FOMC days out) | ln W50 | -0.0083 | 0.0151 | -0.55 | 0.580 | 3859 |
| H1b | FOMC and Fed Chair days out (D-025 a) | ln W50 | -0.0039 | 0.0153 | -0.25 | 0.800 | 3782 |
| H1b | registered (FOMC days out) | ln D5-75 | +0.0287 | 0.0287 | +1.00 | 0.318 | 3859 |
| H1b | FOMC and Fed Chair days out (D-025 a) | ln D5-75 | +0.0308 | 0.0297 | +1.04 | 0.299 | 3782 |
