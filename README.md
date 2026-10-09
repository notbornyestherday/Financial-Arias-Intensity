# Financial Arias Intensity (FAI)

Does *how* intraday volatility is delivered (one burst vs. a slow grind) carry information
that total volatility does not? This project adapts two tools from earthquake engineering
to SPY 1-minute returns: Arias intensity, which on returns reduces to realized variance,
and the Husid curve, which describes how energy accumulates through the day. It then tests
whether timing and a bounded liquidity weighting add anything beyond realized variance.

**Status:** Week 1 of 8, data pipeline. Hypotheses were committed before any data was
downloaded: see [`HYPOTHESES.md`](HYPOTHESES.md) and its commit date. Departures from the
plan are logged in [`DECISIONS.md`](DECISIONS.md).

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest                               # unit tests, incl. recovery of synthetic ground truth

cp .env.example .env                 # add your Alpha Vantage key
python scripts/download.py alphavantage --symbol SPY --start 2009-01 --end 2025-12
python scripts/download.py vix
python scripts/run_all.py --vendor alphavantage --symbol SPY
```

Outputs: `reports/dq_SPY.md` (data-quality report) and `data/processed/SPY_daily.*`
(per-day RV, FAI, Husid timing, W50, variance ratio).

## Layout

```
scripts/      download.py, run_all.py, sim_duration_power.py, sim_h1b_null.py
src/fai/      ingest, sessions, clean, seasonality, husid, measures, sim (done)
              liquidity (Week 3), detection (Week 4), vix (Week 5): stubs
tests/        unit tests; CI runs them on every push
ref/          small hand-maintained tables (FOMC dates)
reports/      computed summaries (no vendor data)
paper/        LaTeX
web/          static Plotly site (Week 4+)
data/         gitignored; recreated by scripts/download.py
```

## Data licensing

Raw vendor data is never committed. The repository contains the scripts that download
it and only derived, per-day measures.
