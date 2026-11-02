# H1b null check on the full pipeline (D-022)

500 simulated samples per scenario, 3850 days each, no reversal anywhere; Newey-West lag 9; seed 22; 397 s.
Pass: rejection rate at most 7.5% and |mean slope| at most 0.25 SD, for W50 and D5-75.
`se_ratio` is the average Newey-West SE over the actual spread of the slopes (about 1 if the SEs are right).

## Verdict by scenario

- A: pass
- B1: pass
- B2: FAIL
- C: pass

## Detail

| scenario | measure | samples | mean_vr | mean_slope | sd_slope | bias_in_sd | se_ratio | reject | verdict |
|---|---|---|---|---|---|---|---|---|---|
| A | w50 | 500 | 0.982 | -0.0005 | +0.0065 | -0.074 | 1.000 | 4.4% | pass |
| A | d5_75 | 500 | 0.982 | -0.0004 | +0.0138 | -0.031 | 0.964 | 5.8% | pass |
| A | d5_95 | 500 | 0.982 | -0.0008 | +0.0244 | -0.033 | 0.931 | 7.2% | (reported only) |
| B1 | w50 | 500 | 0.985 | -0.0008 | +0.0061 | -0.123 | 1.010 | 5.0% | pass |
| B1 | d5_75 | 500 | 0.985 | -0.0010 | +0.0129 | -0.077 | 0.970 | 5.6% | pass |
| B1 | d5_95 | 500 | 0.985 | -0.0016 | +0.0226 | -0.069 | 0.948 | 7.0% | (reported only) |
| B2 | w50 | 500 | 0.934 | +0.0169 | +0.0061 | 2.758 | 1.016 | 78.2% | FAIL |
| B2 | d5_75 | 500 | 0.934 | +0.0165 | +0.0131 | 1.253 | 0.967 | 28.0% | FAIL |
| B2 | d5_95 | 500 | 0.934 | +0.0340 | +0.0235 | 1.445 | 0.956 | 34.0% | (reported only) |
| C | w50 | 500 | 0.983 | -0.0004 | +0.0063 | -0.056 | 1.002 | 4.4% | pass |
| C | d5_75 | 500 | 0.983 | -0.0002 | +0.0132 | -0.015 | 0.964 | 5.4% | pass |
| C | d5_95 | 500 | 0.983 | -0.0005 | +0.0230 | -0.020 | 0.941 | 6.6% | (reported only) |
