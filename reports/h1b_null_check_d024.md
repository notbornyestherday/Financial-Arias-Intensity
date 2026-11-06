# H1b null check for the D-024 fix (VR**)

500 simulated samples per scenario, 3850 days each, no reversal anywhere; Newey-West lag 9; seed 22 (A-D are the D-023 samples); 583 s.
Judged: VR** (`vr_skip2`) on W50 and D5-75 in A, B1, B2, C, D; pass = rejection rate at most 7.5% and |mean slope| at most 0.25 SD. Reported only: D95, and the estimators `vr` (registered VR(30/5)), `vr_skip` (VR*) and `vr_skip_60` (VR*(60/10)).

## Verdict by scenario (VR**)

- A: pass
- B1: pass
- B2: pass
- C: pass
- D: pass

## Detail

| scenario | estimator | measure | samples | mean_vr | mean_slope | sd_slope | bias_in_sd | se_ratio | reject | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| A | vr_skip2 | w50 | 500 | 1.000 | +0.0000 | +0.0027 | 0.010 | 1.064 | 4.0% | pass |
| A | vr_skip2 | d5_75 | 500 | 1.000 | +0.0002 | +0.0055 | 0.039 | 0.976 | 5.6% | pass |
| A | vr_skip2 | d5_95 | 500 | 1.000 | +0.0002 | +0.0088 | 0.025 | 0.959 | 7.8% | (reported: would fail) |
| A | vr | w50 | 500 | 0.982 | -0.0005 | +0.0065 | -0.074 | 1.000 | 4.4% | (reported: would pass) |
| A | vr | d5_75 | 500 | 0.982 | -0.0004 | +0.0138 | -0.031 | 0.964 | 5.8% | (reported: would pass) |
| A | vr | d5_95 | 500 | 0.982 | -0.0008 | +0.0244 | -0.033 | 0.931 | 7.2% | (reported: would pass) |
| A | vr_skip | w50 | 500 | 1.000 | +0.0002 | +0.0043 | 0.046 | 1.008 | 6.4% | (reported: would pass) |
| A | vr_skip | d5_75 | 500 | 1.000 | +0.0000 | +0.0087 | 0.002 | 0.990 | 5.0% | (reported: would pass) |
| A | vr_skip | d5_95 | 500 | 1.000 | -0.0002 | +0.0143 | -0.016 | 0.987 | 4.4% | (reported: would pass) |
| A | vr_skip_60 | w50 | 500 | 1.000 | +0.0001 | +0.0048 | 0.011 | 0.988 | 3.8% | (reported: would pass) |
| A | vr_skip_60 | d5_75 | 500 | 1.000 | +0.0001 | +0.0079 | 0.015 | 0.971 | 6.0% | (reported: would pass) |
| A | vr_skip_60 | d5_95 | 500 | 1.000 | +0.0000 | +0.0113 | 0.002 | 1.003 | 4.4% | (reported: would pass) |
| B1 | vr_skip2 | w50 | 500 | 1.000 | +0.0001 | +0.0026 | 0.029 | 1.050 | 4.2% | pass |
| B1 | vr_skip2 | d5_75 | 500 | 1.000 | +0.0003 | +0.0052 | 0.049 | 0.981 | 4.8% | pass |
| B1 | vr_skip2 | d5_95 | 500 | 1.000 | +0.0003 | +0.0083 | 0.031 | 0.974 | 6.2% | (reported: would pass) |
| B1 | vr | w50 | 500 | 0.985 | -0.0008 | +0.0061 | -0.123 | 1.010 | 5.0% | (reported: would pass) |
| B1 | vr | d5_75 | 500 | 0.985 | -0.0010 | +0.0129 | -0.077 | 0.970 | 5.6% | (reported: would pass) |
| B1 | vr | d5_95 | 500 | 0.985 | -0.0016 | +0.0226 | -0.069 | 0.948 | 7.0% | (reported: would pass) |
| B1 | vr_skip | w50 | 500 | 1.000 | +0.0003 | +0.0040 | 0.068 | 1.028 | 4.6% | (reported: would pass) |
| B1 | vr_skip | d5_75 | 500 | 1.000 | +0.0001 | +0.0082 | 0.018 | 0.994 | 5.6% | (reported: would pass) |
| B1 | vr_skip | d5_95 | 500 | 1.000 | -0.0002 | +0.0135 | -0.014 | 0.993 | 4.4% | (reported: would pass) |
| B1 | vr_skip_60 | w50 | 500 | 1.000 | -0.0000 | +0.0046 | -0.007 | 0.979 | 3.8% | (reported: would pass) |
| B1 | vr_skip_60 | d5_75 | 500 | 1.000 | +0.0002 | +0.0077 | 0.026 | 0.952 | 6.6% | (reported: would pass) |
| B1 | vr_skip_60 | d5_95 | 500 | 1.000 | -0.0000 | +0.0109 | -0.001 | 0.998 | 5.4% | (reported: would pass) |
| B2 | vr_skip2 | w50 | 500 | 1.000 | +0.0000 | +0.0029 | 0.007 | 1.003 | 5.2% | pass |
| B2 | vr_skip2 | d5_75 | 500 | 1.000 | +0.0003 | +0.0053 | 0.048 | 1.000 | 4.4% | pass |
| B2 | vr_skip2 | d5_95 | 500 | 1.000 | +0.0005 | +0.0087 | 0.053 | 0.994 | 5.6% | (reported: would pass) |
| B2 | vr | w50 | 500 | 0.934 | +0.0169 | +0.0061 | 2.758 | 1.016 | 78.2% | (reported: would fail) |
| B2 | vr | d5_75 | 500 | 0.934 | +0.0165 | +0.0131 | 1.253 | 0.967 | 28.0% | (reported: would fail) |
| B2 | vr | d5_95 | 500 | 0.934 | +0.0340 | +0.0235 | 1.445 | 0.956 | 34.0% | (reported: would fail) |
| B2 | vr_skip | w50 | 500 | 0.999 | +0.0006 | +0.0042 | 0.133 | 1.020 | 5.0% | (reported: would pass) |
| B2 | vr_skip | d5_75 | 500 | 0.999 | +0.0004 | +0.0083 | 0.053 | 1.009 | 5.0% | (reported: would pass) |
| B2 | vr_skip | d5_95 | 500 | 0.999 | +0.0008 | +0.0141 | 0.054 | 0.994 | 4.8% | (reported: would pass) |
| B2 | vr_skip_60 | w50 | 500 | 1.000 | +0.0000 | +0.0051 | 0.005 | 0.961 | 6.4% | (reported: would pass) |
| B2 | vr_skip_60 | d5_75 | 500 | 1.000 | +0.0002 | +0.0081 | 0.019 | 0.958 | 7.8% | (reported: would fail) |
| B2 | vr_skip_60 | d5_95 | 500 | 1.000 | +0.0003 | +0.0116 | 0.026 | 1.016 | 3.4% | (reported: would pass) |
| C | vr_skip2 | w50 | 500 | 1.000 | +0.0000 | +0.0027 | 0.007 | 1.029 | 3.8% | pass |
| C | vr_skip2 | d5_75 | 500 | 1.000 | +0.0003 | +0.0054 | 0.052 | 0.935 | 7.4% | pass |
| C | vr_skip2 | d5_95 | 500 | 1.000 | +0.0004 | +0.0087 | 0.043 | 0.921 | 6.2% | (reported: would pass) |
| C | vr | w50 | 500 | 0.983 | -0.0004 | +0.0063 | -0.056 | 1.002 | 4.4% | (reported: would pass) |
| C | vr | d5_75 | 500 | 0.983 | -0.0002 | +0.0132 | -0.015 | 0.964 | 5.4% | (reported: would pass) |
| C | vr | d5_95 | 500 | 0.983 | -0.0005 | +0.0230 | -0.020 | 0.941 | 6.6% | (reported: would pass) |
| C | vr_skip | w50 | 500 | 1.000 | +0.0003 | +0.0042 | 0.073 | 0.995 | 5.6% | (reported: would pass) |
| C | vr_skip | d5_75 | 500 | 1.000 | +0.0001 | +0.0083 | 0.010 | 0.990 | 5.4% | (reported: would pass) |
| C | vr_skip | d5_95 | 500 | 1.000 | +0.0002 | +0.0142 | 0.011 | 0.938 | 7.0% | (reported: would pass) |
| C | vr_skip_60 | w50 | 500 | 1.000 | -0.0001 | +0.0047 | -0.031 | 0.957 | 5.4% | (reported: would pass) |
| C | vr_skip_60 | d5_75 | 500 | 1.000 | +0.0001 | +0.0076 | 0.011 | 0.956 | 6.0% | (reported: would pass) |
| C | vr_skip_60 | d5_95 | 500 | 1.000 | -0.0002 | +0.0111 | -0.020 | 0.967 | 6.6% | (reported: would pass) |
| D | vr_skip2 | w50 | 500 | 0.998 | +0.0005 | +0.0026 | 0.177 | 1.067 | 4.6% | pass |
| D | vr_skip2 | d5_75 | 500 | 0.998 | +0.0004 | +0.0053 | 0.079 | 0.979 | 5.4% | pass |
| D | vr_skip2 | d5_95 | 500 | 0.998 | +0.0007 | +0.0084 | 0.082 | 0.980 | 5.8% | (reported: would pass) |
| D | vr | w50 | 500 | 0.952 | +0.0110 | +0.0060 | 1.826 | 1.010 | 46.2% | (reported: would fail) |
| D | vr | d5_75 | 500 | 0.952 | +0.0090 | +0.0130 | 0.693 | 0.965 | 10.4% | (reported: would fail) |
| D | vr | d5_95 | 500 | 0.952 | +0.0146 | +0.0232 | 0.630 | 0.937 | 11.6% | (reported: would fail) |
| D | vr_skip | w50 | 500 | 0.990 | +0.0023 | +0.0041 | 0.568 | 1.025 | 7.8% | (reported: would fail) |
| D | vr_skip | d5_75 | 500 | 0.990 | +0.0018 | +0.0083 | 0.216 | 0.997 | 6.4% | (reported: would pass) |
| D | vr_skip | d5_95 | 500 | 0.990 | +0.0026 | +0.0137 | 0.192 | 0.994 | 6.2% | (reported: would pass) |
| D | vr_skip_60 | w50 | 500 | 0.998 | +0.0005 | +0.0047 | 0.105 | 0.968 | 5.2% | (reported: would pass) |
| D | vr_skip_60 | d5_75 | 500 | 0.998 | +0.0003 | +0.0076 | 0.039 | 0.968 | 6.4% | (reported: would pass) |
| D | vr_skip_60 | d5_95 | 500 | 0.998 | +0.0005 | +0.0112 | 0.041 | 0.990 | 4.6% | (reported: would pass) |
| D95 | vr_skip2 | w50 | 500 | 0.996 | +0.0008 | +0.0027 | 0.287 | 1.043 | 4.4% | (reported: would fail) |
| D95 | vr_skip2 | d5_75 | 500 | 0.996 | +0.0007 | +0.0052 | 0.135 | 0.991 | 5.8% | (reported: would pass) |
| D95 | vr_skip2 | d5_95 | 500 | 0.996 | +0.0011 | +0.0085 | 0.132 | 0.968 | 6.4% | (reported: would pass) |
| D95 | vr | w50 | 500 | 0.969 | +0.0072 | +0.0061 | 1.182 | 1.000 | 22.6% | (reported: would fail) |
| D95 | vr | d5_75 | 500 | 0.969 | +0.0055 | +0.0130 | 0.421 | 0.968 | 7.4% | (reported: would fail) |
| D95 | vr | d5_95 | 500 | 0.969 | +0.0084 | +0.0225 | 0.372 | 0.956 | 9.0% | (reported: would fail) |
| D95 | vr_skip | w50 | 500 | 0.988 | +0.0026 | +0.0043 | 0.609 | 0.970 | 11.2% | (reported: would fail) |
| D95 | vr_skip | d5_75 | 500 | 0.988 | +0.0018 | +0.0083 | 0.222 | 0.995 | 6.0% | (reported: would pass) |
| D95 | vr_skip | d5_95 | 500 | 0.988 | +0.0027 | +0.0135 | 0.202 | 1.002 | 5.4% | (reported: would pass) |
| D95 | vr_skip_60 | w50 | 500 | 0.995 | +0.0009 | +0.0047 | 0.202 | 0.969 | 5.0% | (reported: would pass) |
| D95 | vr_skip_60 | d5_75 | 500 | 0.995 | +0.0008 | +0.0074 | 0.106 | 0.987 | 7.0% | (reported: would pass) |
| D95 | vr_skip_60 | d5_95 | 500 | 0.995 | +0.0012 | +0.0109 | 0.106 | 1.005 | 4.4% | (reported: would pass) |
