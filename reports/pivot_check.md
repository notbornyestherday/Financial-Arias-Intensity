# Pivot check (D-028)

Written by `scripts/pivot_check.py`; the reading of each outcome was fixed in `paper/interpretation_table.md` before the run.

## Primary: flagged prints removed

Trigger (D-028): corr(ln FAI_w, ln FAI) = **0.9958** over 3,989 test days: at or above 0.95, so the paper reframes around concentration.

| pair | corr | n |
|---|---|---|
| ln FAI_w vs ln FAI (trigger, D-028) | 0.9958 | 3,989 |
| ln FAI_w vs ln RV | 0.4491 | 3,989 |
| FAI_w vs RV (levels) | 0.5092 | 3,989 |
| ln FAI vs ln RV | 0.4326 | 3,989 |
| ln FAI_w(Corwin-Schultz) vs ln FAI | 0.9980 | 3,989 |
| ln FAI_c (floored 1/C) vs ln FAI | 0.8593 | 3,989 |

Why: ln FAI_w = ln FAI + ln f_bar, and ln f_bar (the energy-weighted average damping factor) has SD 0.091 across days against 0.943 for ln FAI; f_bar runs from 1.027 to 1.491 (1st to 99th percentile; bounds 1 and 1.571). Minutes with no liquidity percentile (weighted as typical): 1.3% on average.

## Flagged prints kept

Trigger (D-028): corr(ln FAI_w, ln FAI) = **0.9958** over 3,989 test days: at or above 0.95, so the paper reframes around concentration.

| pair | corr | n |
|---|---|---|
| ln FAI_w vs ln FAI (trigger, D-028) | 0.9958 | 3,989 |
| ln FAI_w vs ln RV | 0.4491 | 3,989 |
| FAI_w vs RV (levels) | 0.5092 | 3,989 |
| ln FAI vs ln RV | 0.4325 | 3,989 |
| ln FAI_w(Corwin-Schultz) vs ln FAI | 0.9980 | 3,989 |
| ln FAI_c (floored 1/C) vs ln FAI | 0.8593 | 3,989 |

Why: ln FAI_w = ln FAI + ln f_bar, and ln f_bar (the energy-weighted average damping factor) has SD 0.091 across days against 0.943 for ln FAI; f_bar runs from 1.027 to 1.491 (1st to 99th percentile; bounds 1 and 1.571). Minutes with no liquidity percentile (weighted as typical): 1.3% on average.
