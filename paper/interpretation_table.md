# Interpretation table (written before any H1 or H2 result)

How each possible outcome of the pre-registered tests (HYPOTHESES.md, with the changes in
DECISIONS.md D-016 to D-036) will be read. Written in advance so the reading cannot be
fitted to the results; it is the skeleton of the Results and Discussion sections.

Drafted in conversation on 2026-11-05 and 2026-11-06 (Esther's answers, lightly edited); H2 rows extended on 2026-11-16 (D-034), before any H2 result.

Across every row: a test is judged on its raw two-sided p at 5%. If it passes raw but not
after the Holm adjustment over the seven confirmatory tests (D-029), the paper calls it
significant before but not after adjustment for multiple tests, and reads it as weaker
evidence.

## H1a: named events (illustrative; n is tiny)

| Outcome | What it would mean |
|---|---|
| All three parts hold (May 6, 2010 and Aug 24, 2015 in the most concentrated 10% for their RV decile; the March 2020 halt days not) | W50 separates liquidity crashes from information-driven stress days of similar total volatility. A calibration check on known cases, not evidence: six hand-picked days whose shape was already known, and it says nothing about reversal (H1b) or forecasting (H2). |
| The crash days are not unusually concentrated | First suspect the measure or the comparison group (the top RV decile is full of crisis days that may be just as concentrated). If those hold up, the crash minutes carried less of the day's energy than their reputation suggests (May 6 was already volatile in the morning). |
| The March 2020 days look concentrated after all | To complete (also check the version without the first 30 minutes, since three of the halts came near the open). |

## H1b: do concentrated days reverse more? (primary measure VR**(30/5), D-024)

| Outcome | What it would mean |
|---|---|
| b > 0, and it holds with D5-75 | Concentrated days partly undo their moves over the next 15-30 minutes, consistent with temporary, liquidity-driven price pressure, and not an artifact of how W50 is defined. Not claimed: that concentration causes reversal, that every concentrated day is a liquidity event, or that it is tradable. |
| b ≈ 0 | Concentration describes how the volatility arrived, not where prices go next, at least over 15-30 minutes. It cannot rule out faster reversals (VR** does not see reversal within about 10-15 minutes), and the test's power is limited, so "no detectable reversal", not "no reversal". |
| b > 0 with only one of W50 and D5-75 | Fragile, under the registered robustness rule (HYPOTHESES.md): reported, not headlined. If only D5-75 holds, the primary measure has failed, so H1b is not supported. The two measures read different things: W50 finds the shortest stretch holding half the day's energy, wherever it sits; D5-75 times the climb from 5% to 75% of the energy, so it spans most of the day's energy, not just its densest part. A burst late in the day after a steady morning is concentrated to W50 and not to D5-75. Follow-up, exploratory and named here in advance: where in the day the W50 windows sit on the days that drive the slope (a cluster in the last half-hour would point at closing-auction order flow, not at liquidity breakdowns in general). |
| b < 0 (concentrated days keep going rather than reverse) | H1b is not supported, and the paper says so plainly. A negative slope is harder to explain away than a positive one: the artifacts found in the null checks (D-022 to D-024: bid-ask bounce, persistent order flow) push b up at realistic spreads, so they cannot make it negative. Two candidate stories, which predict different things after 30 minutes. (i) News: concentrated days are mostly information days (10:00 releases and other news stay in the sample); prices drift for a while as the news is digested, and the move is permanent. (ii) A liquidity spiral: stop-losses, margin calls and forced selling feed on themselves for a while (Brunnermeier and Pedersen, 2009), and the reversal comes later than VR** can see. Two checks, exploratory and named here in advance: the D-024 hour measure VR*(60/10), already reported, sees 20-60 minutes, so under (ii) its slope should be less negative than VR**'s, or positive, as the late reversal enters it, while under (i) it should be negative too; and the same regression without scheduled-release and FOMC days, where (i) predicts the negative slope shrinks. Suggestive, not decisive. H1b failing does not decide H1a or H2. |

## H1c: FOMC days (positive control)

| Outcome | What it would mean |
|---|---|
| Both parts hold (c < 0; the FOMC dummy in the H1b regression is not significantly negative) | The calibration check passes: W50 sees concentration where it is known to exist, and concentration that comes from scheduled news does not come with extra reversal. H1b can be read as a test of concentration. |
| c is not negative (FOMC days are not more concentrated) | As registered: W50 is not measuring concentration, so H1b is reported but not interpreted, whatever its sign; a zero slope could mean "no effect" or "a blind instrument". Suspect the instrument first. The seasonal profile is estimated from prior days, which include earlier FOMC days (meetings are about six weeks apart, so the 60-day window holds one or two), so their 2:00 spikes raise s(τ) around 2:00 and damp the measured concentration of the next FOMC day. This works against the control passing. Exploratory check, named here in advance: the same regression with FOMC days left out of the seasonal profile. |
| c < 0 but the dummy is significantly negative (FOMC days reverse more than their concentration and RV predict) | H1c's premise already says concentration is not exclusive to liquidity; this would say reversal is not either. Scheduled news can overshoot and come back (on FOMC days, a first move at 2:00 that unwinds during the 2:30 press conference, held at every meeting since 2019). The chain behind H1b (concentrated, so it reverses, so it was liquidity) breaks at its last link: a positive b is then read only as "concentrated days reverse more", not as evidence of liquidity breakdowns. Exploratory look, named here in advance: whether the FOMC reversal falls in the press-conference window. |

## H2a / H2b: forecasting next-day VIX

Every H2 regression controls for today's VIX level (D-027), because VIX mean-reverts and the trailing normalization in FAI would otherwise carry that effect; the registered regression without it is reported alongside. X = ln W50 in H2b, so a negative β means a *shorter* window (a more concentrated day) is followed by a bigger VIX rise.

### H2b: concentration (direction not predicted)

| Outcome | What it would mean |
|---|---|
| β < 0 (shorter W50 today, bigger VIX rise tomorrow) | The market charges for jolts: a sudden burst raises the price of protection beyond what RV and the return explain, consistent with traders pricing a higher chance of another jump (VIX leans on out-of-the-money puts, which are crash insurance). |
| β > 0 (longer W50 today, bigger VIX rise tomorrow) | The market charges for grinds: volatility sustained all day reads as stress that is not over (volatility clusters), while a burst reads as a one-off. If H1b also finds that concentrated days reverse, the two fit one story: bursts undo themselves and are not priced. |
| β ≈ 0 | The timing of volatility within the day adds nothing to next-day VIX beyond RV, the return and today's VIX change. |

Because either sign passes H2b in-sample, it is a weaker test than H2a; the out-of-sample test carries more weight here.

### H2a: liquidity weighting

FAI_w is RV after three steps: deseasonalizing, normalizing by the trailing 60 days, and weighting minutes by liquidity (ζ). Unweighted FAI shares the first two, so part (ii) isolates the weighting.

| Outcome | What it would mean |
|---|---|
| (i) and (ii) hold | The weighting carries information about next-day VIX that unweighted FAI does not: energy arriving in thin markets matters more for the price of protection than the same energy in deep ones. The secondary contribution stands, subject to the out-of-sample test. |
| (i) holds, (ii) fails | No evidence that the weighting adds anything: what FAI_w knows comes from the steps it shares with FAI. If FAI_w and FAI are almost perfectly correlated (the pivot check), (ii) has little power, so this reads as "the data cannot separate them", not "the weighting is useless". The paper puts its weight on concentration (H1, H2b). |
| (i) fails | FAI_w adds nothing to next-day VIX beyond RV, the return and VIX's own level and change. The weighting is not supported. |
| The result holds only without the VIX-level control (registered regression passes, D-027 regression fails) | The registered pass came from VIX mean reversion carried by the trailing normalization, not from anything new in FAI_w. Reported as a fail, with both versions shown. |

### Out of sample (2019-2025; both H2a and H2b)

A pass needs both a one-sided Clark-West p below 5% and a lower 2019-2025 MSE for the model with X (D-034).

| Outcome | What it would mean |
|---|---|
| In-sample pass and out-of-sample pass | A forecasting result, within the limits of one market and one period. Statistical, not economic: a lower forecast error is not shown to be tradable, and the size of the improvement is reported next to the test. |
| In-sample pass, out-of-sample fail | Not a forecasting result: the relation fits 2010-2018 but does not carry forward. 2019-2025 holds COVID and 2022, so how VIX reacts may have changed; the paper reports a fail anyway and does not re-split the sample. |
| In-sample fail, out-of-sample pass | Treated as noise and not claimed: a test period can be lucky, and the hypothesis needs both. |
| Clark-West significant, but the model with X has the higher MSE | A fail (D-034). Clark-West is saying X probably carries some information, but in 2019-2025 the forecasts with X were not more accurate. The paper reports both numbers and does not claim a forecasting result. |

### Influence check: leave one year out (exploratory, D-034)

Each in-sample H2 test refitted nine times, leaving out one year of 2010-2018. The verdict comes from the full sample; this row says how to describe it.

| Outcome | What it would mean |
|---|---|
| The result keeps its sign and stays significant in all nine refits | The result describes 2010-2018, not one episode. Reported in one sentence. |
| It loses significance when one year is left out | The paper says which year: "significant, but resting largely on 2018" (or whichever year). The verdict stands; the reading is weaker, and the Discussion names the episode in that year (Volmageddon, the August 2011 downgrade, August 2015) as what the result describes. |
| A null result becomes significant when one year is left out | Not claimed: looking for the year whose removal produces significance is searching. Reported in the table only. |

## Week 3 pivot check: does the weighting change anything? (D-028)

Trigger: correlation of ln FAI_w with ln FAI over the test days, so the only difference between the two is the liquidity weighting. The correlation of FAI_w with RV, in logs and in levels, is reported next to it.

| Outcome | What it would mean |
|---|---|
| 0.95 or above | The weighting barely changes which days look intense, so FAI_w is close to a relabelled FAI. As the brief planned, the paper reframes around concentration (W50, D5-75), which is already the headline; the weighting is reported as a tested idea that did not separate from the unweighted measure, and H2a (ii) is read knowing it has little power. Expected, not a setback. |
| Below 0.95 | The weighting reorders days enough to be worth testing, so H2a (ii) has room to find something. Not a result by itself: a different measure is not a better one, and only H2a and the out-of-sample test can show that. |
| The correlation with RV is near 1 in levels but not in logs | A few crisis days drive the levels figure; the logs figure describes the typical day. Shown only to keep the brief's version visible. |

## Robustness checks (D-018, H3, D-025 a; written 2026-11-17, before the robustness run)

Choices in DECISIONS.md D-036. None of these can change a registered verdict, and none is in the Holm family. D-018 and the Fed Chair version are exploratory; H3 is a registered check whose prediction is no improvement. Drafted by Claude as a study document and settled with Esther's answers the same evening.

### D-018 (a): the benchmarks as controls

H2b (ln W50: t -2.39 in 2010-2018; fails Holm and out of sample).

| Outcome | What it would mean |
|---|---|
| W50 keeps its sign and significance with all three controls | The in-sample link to next-day VIX is about when the energy arrived, not how uneven, jumpy or downward the day was. Still not a forecasting result: H2b failed out of sample and after Holm. One sentence in Results. |
| W50 loses significance with the RQ ratio (alone or with all three) | The link belongs to unevenness, not timing: W50 was standing in for how spiky the day was, whatever the order of the minutes. Timing adds nothing even in sample. Said plainly. |
| W50 loses significance only with jump share | The link belongs to isolated one-minute jumps, not to concentration over many minutes. Consistent with the "jolts" reading of b < 0 (a jump raises the price of crash insurance), but credited to jumps. |
| W50 loses significance only with downside share | The link is about how much energy came from falling minutes: direction, not timing. The regression already controls for the day's return and its downside, so this is an intraday version of the leverage effect. |
| W50 changes sign | Not interpreted: with correlated regressors a sign can flip without meaning much. Table only. |

H1b (ln W50: t -0.55; no effect for the controls to explain).

| Outcome | What it would mean |
|---|---|
| W50 stays not significant | As expected. One sentence. |
| W50 becomes significant only once a benchmark is added | Not claimed: adding controls to a null until it turns significant is searching (the same rule as the leave-one-year-out row). Table only. |

### D-018 (b): each benchmark in place of W50 (2010-2018)

| Outcome | What it would mean |
|---|---|
| A benchmark predicts next-day VIX | A fact about an existing measure, reported as exploratory. If it is jump share, it connects to the jumps literature (Andersen, Bollerslev & Diebold 2007), which is checked before anything is said about it. |
| A benchmark predicts reversal (VR**) | Exploratory. VR** is built to ignore bid-ask bounce, so this would say isolated jumps partly undo themselves over 15-30 minutes. A possible depth item, not a claim. |
| None predicts either | The null is broader than W50: no measure of within-day shape, ordered or not, adds to RV here. One sentence. |

### D-018 (c): out of sample, 2019-2025 (Clark-West p < 5% and R2_OS > 0, as D-034)

W50's row repeats the registered H2b result (a fail) for comparison.

| Outcome | What it would mean |
|---|---|
| No benchmark passes | No measure of within-day shape forecasts next-day VIX beyond RV and VIX's own state. One sentence; it widens the negative result beyond W50. |
| A benchmark passes where W50 fails | Interesting: the information sits in how uneven or jumpy the day was, not in when the energy arrived. Exploratory (three measures, no adjustment for trying three; one market, one period): reported in Results and Discussion and in one line of the conclusion labelled exploratory; in the abstract only if a check registered later confirms it. |

### H3: the differenced signal

A comparison improves if the differenced version passes the registered rule where r~ fails. Holm over the six main comparisons (H1b, H2a (i), H2a (ii), H2b and both out-of-sample tests); D5-75 versions shown, not judged.

| Outcome | What it would mean | Sentence for the paper |
|---|---|---|
| No comparison improves | As predicted | "Replacing the signal with its first difference improves none of the tests." |
| One improves on its raw p but not after Holm | Improves before Holm only: within chance, not a finding | "One of six comparisons passes with the differenced signal, but not after adjusting for the six, which is within what chance would produce." |
| One improves and survives Holm | Not as predicted | "With the differenced signal, [test] passes, even after adjusting for the six comparisons. Because differencing amplifies bid-ask bounce, we do not interpret this until it passes its own simulated null check." |

### Fed Chair version of H1b (D-025 a)

FOMC days and the 83 days in `ref/fed_chair_dates.csv` left out (about 78 fall in 2010-2025, roughly 2% of the H1b sample, so little change is expected). Exploratory because news days concentrate energy without reversing, so leaving them out can only help H1b; the registered sample stays primary and both are reported.

| Outcome | What it would mean |
|---|---|
| b stays near zero (not significant) | Information days were not hiding a reversal effect. One sentence. |
| b becomes significantly positive | Exploratory only; the registered null stands, because the sample was fixed in advance. Read as: news days might mask a small liquidity-reversal effect. Weighed on Nov 20 against the other depth-list candidates, with its own null check if chosen. If only one of W50 and D5-75 agrees, it is fragile under the usual rule. |
| b becomes significantly negative | Concentrated days without Fed Chair news keep going rather than reverse. Read with the H1b b < 0 row: news versus liquidity spiral, with VR*(60/10) as the tie-breaker. Reported, not claimed. |

After the run, every row above is reported as it came out, including the ones that go against the hypotheses.
