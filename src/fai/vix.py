"""H2: next-day VIX changes (HYPOTHESES.md, with D-027 and D-029; renamed from
tests_vix.py, D-006).

The regression, with today's VIX level added by D-027 (the registered version without
``ln_vix`` is reported too):

    d ln VIX_{d+1} = a + b X_d + g1 ln RV_d + g2 r_d + g3 min(r_d, 0)
                     + g4 d ln VIX_d + g5 ln VIX_d + e

Timing: VIX closes at 16:15 ET and SPY's regular session at 16:00, so everything measured
on SPY day d is known before the window of d ln VIX_{d+1} opens.

Data conventions:

* VIX changes run over SPY sessions (D-035): VIX closes on days with no SPY session are
  dropped first, so the change into tomorrow runs from today's close to the VIX close of
  the next SPY session, and today's change from the previous session's. From 2022 Cboe's
  history file carries values on market holidays (from its extended overnight sessions);
  taking the next VIX date instead (the first run, Nov 17) let about 27 out-of-sample
  targets end on a holiday value. ``alignment`` reports the dates dropped and any SPY
  session without a VIX close.
* r_d is SPY's close-to-close log return, from the last regular-hours close of each
  session to the next. Prices are unadjusted (D-010), so on an ex-dividend day the price
  drops by the dividend without any market move; the dividend is added back:
  r_d = ln((C_d + D_d) / C_{d-1}).
* Inference: Newey-West standard errors with the registered lag, through
  ``fai.inference``, the same code the H1 tests use. The intercept is handled by
  demeaning (one group), which gives the same slopes and standard errors as a constant.
* Out of sample: coefficients fitted on 2010-2018 and held fixed over 2019-2025.
  Clark-West (2007) test of equal forecast error against the alternative that the model
  with X forecasts better, one-sided at 5%, Newey-West standard error.
* Secondary (not a hypothesis): logit for a next-day VIX jump, d ln VIX_{d+1} > ln 1.2,
  with the same regressors; HAC sandwich standard errors.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy.special import expit

from .inference import fe_ols, nw_lag, nw_mean, p_two_sided

JUMP = math.log(1.2)                    # secondary logit: VIX up 20% or more the next day

CONTROLS_REGISTERED = ["ln_rv", "r", "r_neg", "dlnvix"]
CONTROLS = CONTROLS_REGISTERED + ["ln_vix"]                      # D-027


# --- data -------------------------------------------------------------------------------

def vix_changes(vix_close: pd.Series) -> pd.DataFrame:
    """ln VIX, today's change and the change into the next VIX close, on VIX's calendar."""
    v = vix_close.astype(float).dropna().sort_index()
    v = v.loc[v > 0]
    lv = np.log(v)
    return pd.DataFrame({"ln_vix": lv, "dlnvix": lv.diff(), "dlnvix_next": lv.shift(-1) - lv})


def last_close(minutes: pd.DataFrame) -> pd.Series:
    """Last regular-hours close of each session, from the cleaned minute table."""
    m = minutes.sort_values(["date", "tau"], kind="stable")
    return m.groupby("date")["close"].last().rename("close")


def close_to_close(close: pd.Series, dividends: pd.Series | None = None) -> pd.Series:
    """r_d = ln((C_d + D_d) / C_{d-1}) over consecutive sessions of ``close``.

    ``dividends``: cash amount per share indexed by ex-dividend date. Ex-dates outside
    the span of ``close`` are ignored; one inside it that is not a session is an error
    (a wrong date would silently leave a price drop in r).
    """
    c = close.astype(float).sort_index()
    add = pd.Series(0.0, index=c.index)
    if dividends is not None and len(dividends):
        div = dividends.astype(float).groupby(level=0).sum()
        div = div.loc[(div.index >= c.index.min()) & (div.index <= c.index.max())]
        stray = div.index.difference(c.index)
        if len(stray):
            raise ValueError("ex-dividend dates that are not sessions: "
                             + ", ".join(str(x.date()) for x in stray))
        add = add.add(div.reindex(c.index).fillna(0.0))
    return np.log((c + add) / c.shift(1)).rename("r")


def h2_frame(daily: pd.DataFrame, close: pd.Series, vix_close: pd.Series,
             dividends: pd.Series | None = None) -> pd.DataFrame:
    """Every H2 variable on SPY days (all sessions in ``daily``; restrict later).

    Logs of the daily measures that exist in ``daily``: fai_w (Amihud, primary), fai,
    w50, d5_75 and, reported alongside (D-030), fai_w_cs and fai_c, plus f_bar.
    """
    f = pd.DataFrame(index=daily.index)
    f["ln_rv"] = np.log(daily["rv"])
    f["r"] = close_to_close(close, dividends).reindex(f.index)
    f["r_neg"] = np.minimum(f["r"], 0.0)
    f = f.join(vix_changes(vix_close.loc[vix_close.index.isin(daily.index)]))   # D-035
    f["jump_next"] = (f["dlnvix_next"] > JUMP).astype(float).where(f["dlnvix_next"].notna())
    for col in ["fai_w", "fai", "w50", "d5_75", "fai_w_cs", "fai_c", "f_bar"]:
        if col in daily.columns:
            with np.errstate(divide="ignore", invalid="ignore"):
                f[f"ln_{col}"] = np.log(daily[col].astype(float))
    for col in ["in_tests", "fomc", "half_day"]:
        if col in daily.columns:
            f[col] = daily[col].astype(bool)
    return f.replace([np.inf, -np.inf], np.nan)


def alignment(spy_days: pd.DatetimeIndex, vix_close: pd.Series) -> dict:
    """Calendar checks over the span of ``spy_days`` (pass every SPY session, half-days
    included): sessions with no VIX close, and VIX dates with no SPY session (market
    holidays; dropped before changes are taken, D-035)."""
    v = vix_close.dropna()
    lo, hi = spy_days.min(), spy_days.max()
    v_in = v.index[(v.index >= lo) & (v.index <= hi)]
    return {"spy_days_without_vix": [str(d.date()) for d in spy_days.difference(v.index)],
            "vix_days_not_spy": [str(d.date()) for d in v_in.difference(spy_days)]}


# --- in-sample regression ---------------------------------------------------------------

def nw_ols(frame: pd.DataFrame, y: str, xs: list[str], lag: int | None = None) -> pd.DataFrame:
    """OLS of ``y`` on ``xs`` with an intercept and Newey-West standard errors.

    Rows must be in time order; incomplete rows are dropped. Returns one row per
    regressor (coef, se, t, p two-sided, n, lag), as ``fai.inference.fe_ols``.
    """
    one_group = np.zeros(len(frame))
    return fe_ols(frame[y], {x: frame[x] for x in xs}, one_group, lag=lag)


def ols_fit(frame: pd.DataFrame, y: str, xs: list[str]) -> pd.Series:
    """Point estimates with the constant, for forecasting (complete rows only)."""
    d = frame[[y, *xs]].dropna()
    Z = np.column_stack([np.ones(len(d)), d[xs].to_numpy(float)])
    beta, *_ = np.linalg.lstsq(Z, d[y].to_numpy(float), rcond=None)
    return pd.Series(beta, index=["const", *xs])


def predict(coef: pd.Series, frame: pd.DataFrame) -> np.ndarray:
    xs = [c for c in coef.index if c != "const"]
    return coef["const"] + frame[xs].to_numpy(float) @ coef[xs].to_numpy(float)


# --- out of sample ----------------------------------------------------------------------

def clark_west(y, yhat_small, yhat_big, lag: int | None = None) -> dict:
    """Clark and West (2007) test for nested forecasts.

    f_t = e_small^2 - (e_big^2 - (yhat_small - yhat_big)^2). The bigger model carries
    extra estimated coefficients whose noise raises its error even when X has nothing to
    say; the last term adds that noise back, so under the null mean(f) is about zero.
    One-sided: a significantly positive mean says the model with X forecasts better.
    Also returned: both mean squared errors and the out-of-sample R^2 of the big model
    against the small one, 1 - MSE_big / MSE_small. The adjusted test can reject while
    MSE_big is above MSE_small in the sample, so both are reported.
    """
    y, a, b = (np.asarray(v, float) for v in (y, yhat_small, yhat_big))
    ok = np.isfinite(y) & np.isfinite(a) & np.isfinite(b)
    y, a, b = y[ok], a[ok], b[ok]
    e1, e2 = y - a, y - b
    f = e1 ** 2 - (e2 ** 2 - (a - b) ** 2)
    m = nw_mean(f, lag=lag)
    mse1, mse2 = float(np.mean(e1 ** 2)), float(np.mean(e2 ** 2))
    return {"cw_mean": m["mean"], "cw_se": m["se"], "cw_t": m["t"],
            "p": 0.5 * math.erfc(m["t"] / math.sqrt(2.0)),        # one-sided, upper tail
            "mse_small": mse1, "mse_big": mse2, "r2_os": 1.0 - mse2 / mse1,
            "n": m["n"], "lag": m["lag"]}


def out_of_sample(frame: pd.DataFrame, y: str, x: str, controls: list[str],
                  fit_mask, test_mask, lag: int | None = None) -> dict:
    """Fit with and without ``x`` on ``fit_mask`` rows, forecast ``test_mask`` rows with
    the coefficients held fixed, and compare by Clark-West. Both models use the same
    rows (complete for every column, ``x`` included)."""
    cols = [y, x, *controls]
    fit = frame.loc[np.asarray(fit_mask, bool), cols].dropna()
    test = frame.loc[np.asarray(test_mask, bool), cols].dropna()
    small, big = ols_fit(fit, y, controls), ols_fit(fit, y, [x, *controls])
    res = clark_west(test[y], predict(small, test), predict(big, test), lag=lag)
    res.update({"x": x, "beta_fit": float(big[x]), "n_fit": len(fit),
                "test_start": _day(test.index.min()), "test_end": _day(test.index.max())})
    return res


def _day(v) -> str:
    return str(v.date()) if hasattr(v, "date") else str(v)


# --- secondary: jump logit --------------------------------------------------------------

def logit_hac(frame: pd.DataFrame, y: str, xs: list[str], lag: int | None = None,
              max_iter: int = 100, tol: float = 1e-9) -> pd.DataFrame:
    """Logit by Newton-Raphson (with step halving), HAC sandwich standard errors.

    Returns one row per coefficient (const first): coef, se, t, p, n, events, lag,
    converged. Rows must be in time order; incomplete rows are dropped. With too few
    events the estimates may not exist (perfect separation): then ``converged`` is False
    and the standard errors are NaN rather than a number that means nothing.
    """
    d = frame[[y, *xs]].dropna()
    yy = d[y].to_numpy(float)
    Z = np.column_stack([np.ones(len(d)), d[xs].to_numpy(float)])
    n, events = len(yy), int(yy.sum())
    L = nw_lag(n) if lag is None else int(lag)
    names = ["const", *xs]
    nan = np.full(Z.shape[1], np.nan)

    def out(beta, se, converged):
        t = beta / se
        return pd.DataFrame({"coef": beta, "se": se, "t": t,
                             "p": [p_two_sided(v) if np.isfinite(v) else np.nan for v in t],
                             "n": n, "events": events, "lag": L, "converged": converged},
                            index=names)

    if events == 0 or events == n:
        return out(nan, nan, False)

    def loglik(b):
        eta = Z @ b
        return float(np.sum(yy * eta - np.logaddexp(0.0, eta)))

    beta = np.zeros(Z.shape[1])
    beta[0] = math.log(yy.mean() / (1 - yy.mean()))
    converged = False
    for _ in range(max_iter):
        p = expit(Z @ beta)
        H = Z.T @ (Z * (p * (1 - p))[:, None])
        try:
            step = np.linalg.solve(H, Z.T @ (yy - p))
        except np.linalg.LinAlgError:
            break
        ll0, s = loglik(beta), 1.0
        while loglik(beta + s * step) < ll0 - 1e-12 and s > 1e-8:
            s /= 2
        beta = beta + s * step
        if np.max(np.abs(s * step)) < tol:
            converged = True
            break
    if not converged:
        return out(beta, nan, False)
    p = expit(Z @ beta)
    H = Z.T @ (Z * (p * (1 - p))[:, None])
    U = Z * (yy - p)[:, None]
    S = U.T @ U
    for k in range(1, L + 1):
        G = U[k:].T @ U[:-k]
        S += (1 - k / (L + 1)) * (G + G.T)
    Hinv = np.linalg.inv(H)
    return out(beta, np.sqrt(np.diag(Hinv @ S @ Hinv)), True)
