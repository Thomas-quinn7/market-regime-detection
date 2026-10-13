"""Why the two-state HMM forecasts volatility worse than trailing volatility does.

Run from the repo root (a few minutes; the walk-forwards dominate):

    python examples/why_hmm_loses.py

Part 1 takes the walk-forward return HMM on the S&P 500, 2005-2023, and measures where its
forecast loses information compared with EWMA volatility, which sees exactly the same returns:

- saturation: how often the filtered high-vol probability is pinned near 0 or 1;
- the HMM is a squashed EWMA: how closely the probability tracks EWMA vol in rank;
- information inside a state: on days the HMM is sure of the high state, does EWMA vol still rank
  next-month vol? Whatever it still explains there, the HMM's single answer for the state throws away;
- the ceiling: the HMM's forecast cannot go above the stressed state's vol, however bad things get;
- whipsaw: how many high-state episodes last a week or less.

Part 2 is a controlled experiment on simulated returns, where the truth is known. The same
walk-forward HMM and the same baselines are run on two made-up markets with similar average vol:

- A, continuous: log volatility drifts as a persistent AR(1), with no regimes at all;
- B, two-state: volatility really does switch between a calm and a stressed level.

Each market is simulated with five seeds (5,000 days each). If the HMM loses in A and holds up in
B, the problem is the mismatch between a two-state model and a market whose volatility moves
continuously, rather than the estimation.

Uses only S&P 500 returns from Yahoo, the repo's development period. Nothing here is a holdout.
"""
from __future__ import annotations

import warnings
from pathlib import Path

import matplotlib
import matplotlib.ticker

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from regimes.data import load_index_returns  # noqa: E402
from regimes.evaluate import ewma_vol, walk_forward_oos  # noqa: E402
from regimes.forecast import (  # noqa: E402
    forecast_losses,
    forward_vol,
    har_features,
    walk_forward_regression,
)

START, END = "2005-01-01", "2023-12-31"
H = 21
SEEDS = (1, 2, 3, 4, 7)
FIG_DIR = Path(__file__).resolve().parents[1] / "docs" / "figures"


def _episode_lengths(on: pd.Series) -> np.ndarray:
    run = (on != on.shift()).cumsum()
    lengths = on.groupby(run).agg(["first", "size"])
    return lengths.loc[lengths["first"], "size"].to_numpy()


def _calibrated(target: pd.Series, signals: dict[str, pd.DataFrame | pd.Series]) -> pd.DataFrame:
    """Every signal through the same embargoed log-scale walk-forward calibration, on common rows."""
    common = pd.concat(signals.values(), axis=1).dropna().index
    fc = {k: walk_forward_regression(target, X.reindex(common), horizon=H, step=63, min_rows=756,
                                     log_target=True).forecast for k, X in signals.items()}
    return pd.concat({"y": target, **fc}, axis=1, sort=True).dropna()


def _run(returns: pd.Series) -> dict:
    wf = walk_forward_oos(returns, min_train=756, step=63, horizon=H)
    ewma = ewma_vol(returns)
    target = forward_vol(returns, H)
    joined = _calibrated(target, {
        "EWMA vol": np.log(ewma).rename("ewma"),
        "HAR": np.log(har_features(returns).clip(lower=1e-3)),
        "HMM implied vol": np.log(wf.implied_vol).rename("hmm_iv"),
        "HMM probability": wf.high_vol_prob,
    })
    return {"wf": wf, "ewma": ewma, "target": target, "joined": joined}


def part1(returns: pd.Series) -> dict:
    out = _run(returns)
    wf, ewma, target = out["wf"], out["ewma"], out["target"]
    p = wf.high_vol_prob
    d = pd.DataFrame({"p": p, "ewma": ewma, "iv": wf.implied_vol, "y": target}).dropna()
    print(f"walk-forward HMM: {len(p)} out-of-sample days, {p.index.min().date()} -> "
          f"{p.index.max().date()}; {len(d)} with a known next-month vol")

    lo, hi = (d.p < 0.05).mean(), (d.p > 0.95).mean()
    print("\n1) saturation")
    print(f"  probability below 0.05 on {lo:.0%} of days, above 0.95 on {hi:.0%}, "
          f"in between on {1 - lo - hi:.0%}")

    print("\n2) the HMM is a squashed EWMA")
    print(f"  rank correlation of the probability with EWMA vol: {d.p.corr(d.ewma, 'spearman'):.2f}")
    bins = pd.qcut(d.ewma.rank(pct=True), 10, labels=False)
    print("  mean probability by EWMA-vol decile: "
          + " ".join(f"{v:.2f}" for v in d.groupby(bins).p.mean()))

    print("\n3) information left inside a state (rank correlation, EWMA vol vs next-month vol)")
    rows = {}
    for name, mask in [("all days", d.p.notna()), ("HMM sure of calm (p < 0.05)", d.p < 0.05),
                       ("HMM sure of stress (p > 0.95)", d.p > 0.95)]:
        s = d[mask]
        rows[name] = {"days": len(s), "EWMA vs next-month vol": s.ewma.corr(s.y, "spearman"),
                      "HMM prob vs next-month vol": s.p.corr(s.y, "spearman"),
                      "next-month vol, 10th pct": s.y.quantile(0.1),
                      "next-month vol, 90th pct": s.y.quantile(0.9)}
    print(pd.DataFrame(rows).T.round(2).to_string())

    print("\n4) the ceiling (daily %)")
    for q in (0.5, 0.9, 0.99, 1.0):
        print(f"  quantile {q:.2f}: next-month vol {d.y.quantile(q):.2f}, HMM implied vol "
              f"{d.iv.quantile(q):.2f}, EWMA vol {d.ewma.quantile(q):.2f}")
    worst = d.y.idxmax()
    print(f"  worst month starts {worst.date()}: realised {d.y[worst]:.2f}, HMM forecast "
          f"{d.iv[worst]:.2f}, EWMA {d.ewma[worst]:.2f}")

    on = p >= 0.5
    ep = _episode_lengths(on)
    print("\n5) whipsaw")
    print(f"  {len(ep)} high-state episodes, {on.astype(int).diff().abs().sum() / (len(on) / 252):.1f} "
          f"switches a year; {np.mean(ep <= 5):.0%} last 5 days or less, median length "
          f"{np.median(ep):.0f} days")

    print("\ncalibrated forecasts, same days:")
    j = out["joined"]
    print(forecast_losses({k: j[k] for k in j if k != "y"}, j["y"]).drop(columns="n")
          .round(3).to_string())
    return {**out, "d": d}


def _simulate(kind: str, n: int, seed: int) -> pd.Series:
    rng = np.random.default_rng(seed)
    if kind == "continuous":
        phi, sd_log = 0.985, 0.45
        eta = rng.normal(0, sd_log * np.sqrt(1 - phi ** 2), n)
        log_sig = np.empty(n)
        log_sig[0] = 0.0
        for t in range(1, n):
            log_sig[t] = phi * log_sig[t - 1] + eta[t]
        sig = 0.9 * np.exp(log_sig)
    else:
        levels, stay = np.array([0.7, 1.8]), np.array([0.99, 0.97])
        state = np.empty(n, dtype=int)
        state[0] = 0
        u = rng.random(n)
        for t in range(1, n):
            state[t] = state[t - 1] if u[t] < stay[state[t - 1]] else 1 - state[t - 1]
        sig = levels[state]
    idx = pd.bdate_range("2000-01-03", periods=n)
    return pd.Series(sig * rng.standard_normal(n), index=idx, name="r")


def part2() -> pd.DataFrame:
    print("\n=== Part 2: simulated markets, same HMM, same baselines")
    rows = []
    for kind in ("continuous", "two-state"):
        for seed in SEEDS:
            j = _run(_simulate(kind, 5000, seed))["joined"]
            rmse = forecast_losses({k: j[k] for k in j if k != "y"}, j["y"])["rmse"]
            rows.append({"market": kind, "seed": seed, **rmse.to_dict()})
            print(f"  {kind}, seed {seed}: " + ", ".join(f"{k} {v:.3f}" for k, v in rmse.items()),
                  flush=True)
    out = pd.DataFrame(rows)
    hmm_best = out[["HMM implied vol", "HMM probability"]].min(axis=1)
    out["HMM beats both baselines"] = hmm_best < out[["EWMA vol", "HAR"]].min(axis=1)
    return out


def _log_axis(axis, ticks=(0.5, 1, 2, 4)) -> None:
    axis.set_major_locator(matplotlib.ticker.FixedLocator(ticks))
    axis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%g"))
    axis.set_minor_formatter(matplotlib.ticker.NullFormatter())


def figure(res: dict) -> Path:
    d, j = res["d"], res["joined"]
    fig, ax = plt.subplots(2, 2, figsize=(12, 8.5))

    a = ax[0, 0]
    a.hist(d.p, bins=40, color="#4c72b0")
    a.set_title("1. The probability is nearly always pinned at 0 or 1")
    a.set_xlabel("filtered high-vol probability")
    a.set_ylabel("days")

    a = ax[0, 1]
    a.scatter(d.ewma, d.p, s=3, alpha=0.25, color="#4c72b0")
    a.set_xscale("log")
    _log_axis(a.xaxis, (0.3, 0.5, 1, 2, 4))
    a.set_title("2. It is a squashed version of EWMA vol")
    a.set_xlabel("EWMA vol, daily % (log scale)")
    a.set_ylabel("filtered high-vol probability")

    a = ax[1, 0]
    s = d[d.p > 0.95]
    a.scatter(s.ewma, s.y, s=4, alpha=0.35, color="#c44e52", label="EWMA vol (varies)")
    a.scatter(s.ewma, s.iv, s=4, alpha=0.35, color="#55a868", label="HMM forecast (near flat)")
    lim = [s[["ewma", "y"]].min().min(), s[["ewma", "y"]].max().max()]
    a.plot(lim, lim, color="grey", lw=0.8, ls="--")
    a.set_xscale("log")
    a.set_yscale("log")
    _log_axis(a.xaxis)
    _log_axis(a.yaxis)
    a.set_title("3. Days the HMM is sure of stress: next-month vol still varies about 4x")
    a.set_xlabel("EWMA vol today, daily %")
    a.set_ylabel("next-month realised vol, daily %")
    a.legend(loc="upper left", fontsize=8, markerscale=3)

    a = ax[1, 1]
    w = slice("2019-10-01", "2020-12-31")
    a.plot(res["target"].loc[w], color="black", lw=1.6,
           label="realised vol over the next month (the target)")
    a.plot(d.iv.loc[w], color="#55a868", lw=1.2, label="HMM implied vol")
    a.plot(j["HAR"].loc[w], color="#dd8452", lw=1.2, label="HAR, calibrated")
    a.plot(d.ewma.loc[w], color="#c44e52", lw=1.0, ls=":", label="EWMA vol")
    a.set_title("4. 2020: the HMM forecast is stuck between a floor and a ceiling")
    a.set_ylabel("daily %")
    a.legend(fontsize=8)
    a.tick_params(axis="x", rotation=30)

    fig.suptitle("Why the two-state HMM loses to simpler volatility measures (S&P 500, walk-forward)")
    fig.tight_layout()
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    path = FIG_DIR / "why_hmm_loses.png"
    fig.savefig(path, dpi=140)
    return path


def main() -> None:
    warnings.simplefilter("ignore")
    returns = load_index_returns(start=START, end=END)
    print(f"=== Part 1: S&P 500, {len(returns)} days, {returns.index.min().date()} -> "
          f"{returns.index.max().date()}")
    res = part1(returns)
    sim = part2()
    print("\nmean RMSE over the seeds (lower is better), and how often the HMM beat both baselines:")
    summary = sim.groupby("market")[["EWMA vol", "HAR", "HMM implied vol", "HMM probability"]].mean()
    summary["HMM wins"] = sim.groupby("market")["HMM beats both baselines"].sum().astype(int)
    print(summary.round(3).to_string())
    print(f"\nfigure written to {figure(res)}")


if __name__ == "__main__":
    main()
