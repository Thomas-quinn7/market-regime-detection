"""Intraday realised vol: session window, sampling grid, DST and the two-instrument guard."""
import numpy as np
import pandas as pd

from regimes.intraday import daily_realised_vol


def _session(day: str, seed: int, *, instrument: int = 1, volume: float = 100.0) -> pd.DataFrame:
    """One-minute bars from 08:00 to 17:00 New York time (so some fall outside the session)."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range(f"{day} 08:00", f"{day} 16:59", freq="1min", tz="America/New_York")
    close = 4000.0 * np.exp(np.cumsum(rng.normal(0, 0.0005, len(idx))))
    open_ = np.concatenate([[4000.0], close[:-1]])
    df = pd.DataFrame({"open": open_, "close": close, "volume": volume,
                       "instrument_id": instrument}, index=idx.tz_convert("UTC"))
    return df


def _expected(df: pd.DataFrame) -> float:
    ny = df.tz_convert("America/New_York") if df.index.tz else df
    rth = ny.between_time("09:30", "16:00", inclusive="left")
    closes = rth["close"].to_numpy()[4::5]  # close of 09:34, 09:39, ..., 15:59
    prices = np.concatenate([[rth["open"].iloc[0]], closes])
    return float(np.sqrt(((np.diff(np.log(prices)) * 100) ** 2).sum()))


def test_rv_matches_five_minute_sum_and_ignores_out_of_session_bars():
    df = _session("2024-01-10", 0)
    out = daily_realised_vol(df)
    assert out["n_returns"].iloc[0] == 78
    assert np.isclose(out["rv"].iloc[0], _expected(df))


def test_session_is_new_york_time_across_dst():
    # 8 March 2024 is EST (UTC-5); 11 March 2024 is EDT (UTC-4). Both must give 78 returns.
    df = pd.concat([_session("2024-03-08", 1), _session("2024-03-11", 2)])
    out = daily_realised_vol(df)
    assert list(out["n_returns"]) == [78, 78]


def test_minor_instrument_in_a_session_is_dropped():
    main = _session("2024-01-10", 3, instrument=1, volume=1000.0)
    other = _session("2024-01-10", 4, instrument=2, volume=1.0)
    other["close"] *= 1.05  # a different contract at a different price level
    out = daily_realised_vol(pd.concat([main, other]).sort_index())
    assert np.isclose(out["rv"].iloc[0], _expected(main))


def test_semivariances_add_up_and_quarticity_is_one_for_constant_moves():
    out = daily_realised_vol(_session("2024-01-10", 5)).iloc[0]
    assert np.isclose(out["rv_neg"] ** 2 + out["rv_pos"] ** 2, out["rv"] ** 2)
    # Equal-sized moves: sum(r^4) = n * a^4 and RV^2 = n * a^2, so sqrt(RQ) / RV^2 = 1 / sqrt(3)
    # exactly. (For Gaussian moves it is about 1, since E[r^4] = 3 sigma^4.)
    idx = pd.date_range("2024-01-10 09:30", "2024-01-10 15:59", freq="1min", tz="America/New_York")
    step = np.where(np.arange(len(idx)) // 5 % 2 == 0, 1.0, -1.0) * 0.0002
    close = 4000.0 * np.exp(np.cumsum(step))
    flat = pd.DataFrame({"open": np.concatenate([[4000.0], close[:-1]]), "close": close,
                         "volume": 100.0}, index=idx.tz_convert("UTC"))
    day = daily_realised_vol(flat).iloc[0]
    assert np.isclose(np.sqrt(day["rq"]) / day["rv"] ** 2, 1 / np.sqrt(3))
