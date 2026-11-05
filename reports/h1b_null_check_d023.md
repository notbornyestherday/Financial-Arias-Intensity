# H1b null check for the D-023 fix (VR*)

500 simulated samples per scenario, 3850 days each, no reversal anywhere; Newey-West lag 9; seed 22 (A-C are the D-022 samples); 658 s.
Judged: VR* (`vr_skip`) on W50 and D5-75; pass = rejection rate at most 7.5% and |mean slope| at most 0.25 SD. The registered VR(30/5) (`vr`) is reported alongside.

## Verdict by scenario (VR*)

- A: pass
- B1: pass
- B2: pass
- C: pass
- D: FAIL

## Detail

| scenario | estimator | measure | samples | mean_vr | mean_slope | sd_slope | bias_in_sd | se_ratio | reject | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| A | vr_skip | w50 | 500 | 1.000 | +0.0002 | +0.0043 | 0.046 | 1.008 | 6.4% | pass |
| A | vr_skip | d5_75 | 500 | 1.000 | +0.0000 | +0.0087 | 0.002 | 0.990 | 5.0% | pass |
| A | vr_skip | d5_95 | 500 | 1.000 | -0.0002 | +0.0143 | -0.016 | 0.987 | 4.4% | (reported only) |
| A | vr | w50 | 500 | 0.982 | -0.0005 | +0.0065 | -0.074 | 1.000 | 4.4% | (reported only) |
| A | vr | d5_75 | 500 | 0.982 | -0.0004 | +0.0138 | -0.031 | 0.964 | 5.8% | (reported only) |
| A | vr | d5_95 | 500 | 0.982 | -0.0008 | +0.0244 | -0.033 | 0.931 | 7.2% | (reported only) |
| B1 | vr_skip | w50 | 500 | 1.000 | +0.0003 | +0.0040 | 0.068 | 1.028 | 4.6% | pass |
| B1 | vr_skip | d5_75 | 500 | 1.000 | +0.0001 | +0.0082 | 0.018 | 0.994 | 5.6% | pass |
| B1 | vr_skip | d5_95 | 500 | 1.000 | -0.0002 | +0.0135 | -0.014 | 0.993 | 4.4% | (reported only) |
| B1 | vr | w50 | 500 | 0.985 | -0.0008 | +0.0061 | -0.123 | 1.010 | 5.0% | (reported only) |
| B1 | vr | d5_75 | 500 | 0.985 | -0.0010 | +0.0129 | -0.077 | 0.970 | 5.6% | (reported only) |
| B1 | vr | d5_95 | 500 | 0.985 | -0.0016 | +0.0226 | -0.069 | 0.948 | 7.0% | (reported only) |
| B2 | vr_skip | w50 | 500 | 0.999 | +0.0006 | +0.0042 | 0.133 | 1.020 | 5.0% | pass |
| B2 | vr_skip | d5_75 | 500 | 0.999 | +0.0004 | +0.0083 | 0.053 | 1.009 | 5.0% | pass |
| B2 | vr_skip | d5_95 | 500 | 0.999 | +0.0008 | +0.0141 | 0.054 | 0.994 | 4.8% | (reported only) |
| B2 | vr | w50 | 500 | 0.934 | +0.0169 | +0.0061 | 2.758 | 1.016 | 78.2% | (reported only) |
| B2 | vr | d5_75 | 500 | 0.934 | +0.0165 | +0.0131 | 1.253 | 0.967 | 28.0% | (reported only) |
| B2 | vr | d5_95 | 500 | 0.934 | +0.0340 | +0.0235 | 1.445 | 0.956 | 34.0% | (reported only) |
| C | vr_skip | w50 | 500 | 1.000 | +0.0003 | +0.0042 | 0.073 | 0.995 | 5.6% | pass |
| C | vr_skip | d5_75 | 500 | 1.000 | +0.0001 | +0.0083 | 0.010 | 0.990 | 5.4% | pass |
| C | vr_skip | d5_95 | 500 | 1.000 | +0.0002 | +0.0142 | 0.011 | 0.938 | 7.0% | (reported only) |
| C | vr | w50 | 500 | 0.983 | -0.0004 | +0.0063 | -0.056 | 1.002 | 4.4% | (reported only) |
| C | vr | d5_75 | 500 | 0.983 | -0.0002 | +0.0132 | -0.015 | 0.964 | 5.4% | (reported only) |
| C | vr | d5_95 | 500 | 0.983 | -0.0005 | +0.0230 | -0.020 | 0.941 | 6.6% | (reported only) |
| D | vr_skip | w50 | 500 | 0.990 | +0.0023 | +0.0041 | 0.568 | 1.025 | 7.8% | FAIL |
| D | vr_skip | d5_75 | 500 | 0.990 | +0.0018 | +0.0083 | 0.216 | 0.997 | 6.4% | pass |
| D | vr_skip | d5_95 | 500 | 0.990 | +0.0026 | +0.0137 | 0.192 | 0.994 | 6.2% | (reported only) |
| D | vr | w50 | 500 | 0.952 | +0.0110 | +0.0060 | 1.826 | 1.010 | 46.2% | (reported only) |
| D | vr | d5_75 | 500 | 0.952 | +0.0090 | +0.0130 | 0.693 | 0.965 | 10.4% | (reported only) |
| D | vr | d5_95 | 500 | 0.952 | +0.0146 | +0.0232 | 0.630 | 0.937 | 11.6% | (reported only) |
