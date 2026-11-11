"""Rebuild every number and chart input from data/raw/. No network.

Follows PREREGISTRATION.md. Outputs:
  data/processed/results.json   every number quoted anywhere
  docs/data.js                  the same, for the static dashboard
  THESIS.md                     rendered from THESIS.template.md
  README.md                     rendered from README.template.md
  docs/thesis.html              the same thesis as a web page
  docs/predictions.html         the rating and its calls, with RATING.md as timestamped
"""
import json, os, re, sys
import markdown
import numpy as np
import pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RAW = os.path.join(ROOT, "data", "raw")

E0, T, E2 = pd.Timestamp("2026-09-08"), pd.Timestamp("2026-09-29"), pd.Timestamp("2026-10-01")
EST_START, EST_END = pd.Timestamp("2026-06-01"), pd.Timestamp("2026-09-07")
EST_LEN, GAP, HORIZON = 99, 21, 28  # days: estimation window, gap before event, event window
LAST_DAY = pd.Timestamp(os.environ.get("LAST_DAY", "2026-11-09"))  # last complete UTC day; set LAST_DAY=YYYY-MM-DD after a refetch
PAUSED = ["Binance", "Polygon", "TON", "Optimism", "Avalanche", "Stellar", "Monad", "X Layer", "ADI"]  # Scroll, Plasma: not reported by DefiLlama
DONORS_PREREG = ["thorchain-dex", "chainflip-amm", "maya-protocol", "li.fi-bridge-aggregator",
                 "socket-protocol", "jumper-bridge-aggregator", "0x-bridge-aggregator", "rango"]


def raw(name):
    with open(os.path.join(RAW, name + ".json")) as f:
        return json.load(f)


def write(path, text):
    with open(path, "w") as f:
        f.write(text)


def llama_series(name):
    s = pd.Series({pd.Timestamp(t, unit="s").normalize(): float(v) for t, v in raw(name)["totalDataChart"]})
    return s[s.index <= LAST_DAY].sort_index()


def market(coin):
    """CoinGecko stamps a day's close and trailing-24h volume at the next midnight, so shift back one day."""
    d = raw("market_" + coin)
    out = {}
    for key, col in (("prices", "price"), ("total_volumes", "volume"), ("market_caps", "mcap")):
        s = pd.Series({pd.Timestamp(t, unit="ms"): v for t, v in d[key]})
        s = s[s.index == s.index.normalize()]  # drop the intraday "now" point
        s.index = s.index - pd.Timedelta(days=1)
        out[col] = s
    return pd.DataFrame(out)


def balances():
    """Token units held by the protocol at the start of each UTC day: total and per chain."""
    d = raw("intents_balances")

    def frame(rows):
        f = pd.DataFrame({pd.Timestamp(r["date"], unit="s").normalize(): r["tokens"] for r in rows
                          if pd.Timestamp(r["date"], unit="s") == pd.Timestamp(r["date"], unit="s").normalize()}).T
        return f.sort_index()

    def merge_near(f):  # DefiLlama labels the same asset NEAR on some days and WNEAR on others
        f["NEAR"] = f.reindex(columns=["NEAR", "WNEAR"]).sum(axis=1)
        return f.drop(columns="WNEAR", errors="ignore")

    total = merge_near(frame(d["tokens"]))
    usd = merge_near(frame(d["tokensInUsd"]))
    chains = {c: merge_near(frame(v["tokens"])) for c, v in d["chainTvls"].items()}
    return total, usd, chains


def ols(y, X):
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta


def abnormal(y, X, est, evt):
    """Fit on est rows, return (mean abnormal over evt, full abnormal series)."""
    beta = ols(y[est].values, X[est].values)
    ab = y - (X * beta).sum(axis=1, skipna=False)
    return float(ab[evt].mean()), ab


def design(panel, donors, est):
    """Regressors: constant, log donor index (each donor scaled by its estimation-window mean), log NEAR and ZEC spot volume."""
    idx = (panel[donors] / panel.loc[est, donors].mean()).mean(axis=1)
    return pd.DataFrame({"const": 1.0, "log_donor_index": np.log(idx),
                         "log_near_spot_vol": np.log(panel["near_vol"]), "log_zec_spot_vol": np.log(panel["zec_vol"])}, index=panel.index)


def event_stat(panel, col, donors, event, horizon=HORIZON):
    est_end = event - pd.Timedelta(days=GAP + 1)
    est_start = est_end - pd.Timedelta(days=EST_LEN - 1)
    est = (panel.index >= est_start) & (panel.index <= est_end)
    evt = (panel.index >= event) & (panel.index < event + pd.Timedelta(days=horizon))
    X = design(panel, donors, est)
    return abnormal(np.log(panel[col]), X, est, evt)


def simplex_fit(y, D, iters=20000, lr=0.5):
    """Non-negative weights summing to one that minimise ||y - D w||^2 (exponentiated gradient)."""
    w = np.full(D.shape[1], 1 / D.shape[1])
    for _ in range(iters):
        g = D.T @ (D @ w - y) / len(y)
        w = w * np.exp(-lr * g)
        w /= w.sum()
    return w


def synthetic(panel, treated, pool, est, evt):
    """Synthetic control on volumes scaled by their estimation-window means. Returns (event-window ratio - 1, weights, synthetic series)."""
    scaled = panel[[treated] + pool] / panel.loc[est, [treated] + pool].mean()
    w = simplex_fit(scaled.loc[est, treated].values, scaled.loc[est, pool].values)
    synth = (scaled[pool] * w).sum(axis=1, skipna=False)
    ratio = scaled.loc[evt, treated].sum() / synth[evt].sum() - 1
    return float(ratio), dict(zip(pool, map(float, w))), synth, scaled[treated]


def pct(x):
    return float(np.exp(x) - 1)


def logchg(s, a, b):
    return float(np.log(s[b] / s[a]))


def placebo_changes(s, starts, days):
    return np.array([np.log(s[d + pd.Timedelta(days=days)] / s[d]) for d in starts])


def main():
    R = {"events": {"E0": str(E0.date()), "T": str(T.date()), "E2": str(E2.date())}, "last_day": str(LAST_DAY.date())}

    # ---- panel -----------------------------------------------------------------
    panel = pd.DataFrame({"volume": llama_series("intents_volume"), "fees": llama_series("intents_fees"),
                          "revenue": llama_series("intents_revenue")})
    for d in DONORS_PREREG:
        panel[d] = llama_series("donor_" + d)
    near, zec, btc = market("near"), market("zcash"), market("bitcoin")
    panel["near_vol"], panel["zec_vol"] = near.volume, zec.volume
    panel["near_price"], panel["zec_price"], panel["btc_price"] = near.price, zec.price, btc.price
    panel = panel[(panel.index >= near.index.min()) & (panel.index <= LAST_DAY)]
    # Fail fast: a short or stale download must not be scored as if it reached LAST_DAY.
    assert panel["volume"].index.max() == LAST_DAY and panel["volume"].notna().all(), f"DefiLlama volume does not reach {LAST_DAY.date()}"

    est = (panel.index >= EST_START) & (panel.index <= EST_END)
    evt = (panel.index >= T) & (panel.index < T + pd.Timedelta(days=HORIZON))
    assert est.sum() == EST_LEN and evt.sum() == HORIZON

    # Donor rule: usable only with a positive value on every day the design touches.
    first_needed = panel.index.min()
    dropped = {}
    for d in DONORS_PREREG:
        s = panel[d]
        if s[est].isna().any() or (s[est] <= 0).any():
            dropped[d] = "missing days in the estimation window (pre-registered rule)" if s[est].isna().any() else "zero-volume days in the estimation window (deviation 1)"
        elif s[first_needed:EST_END].isna().any():
            dropped[d] = "does not cover the placebo windows (deviation 1)"
    donors = [d for d in DONORS_PREREG if d not in dropped]
    R["donors"] = {"used": donors, "dropped": dropped}
    panel[donors] = panel[donors].where(panel[donors] > 0)  # a zero day would make the index undefined
    # A donor may miss a day outside the windows (the index then averages the rest); never inside one.
    assert not panel.loc[(panel.index <= EST_END) | evt, donors].isna().any().any(), "donor gap inside a window"

    # ---- H1 / H2: abnormal volume and fees ---------------------------------------
    first_placebo = panel.index.min() + pd.Timedelta(days=EST_LEN + GAP)
    last_placebo = E0 - pd.Timedelta(days=HORIZON)
    placebo_dates = pd.date_range(first_placebo, last_placebo)
    for col, key in (("volume", "H1"), ("fees", "H2")):
        stat, ab = event_stat(panel, col, donors, T)
        plc = np.array([event_stat(panel, col, donors, p)[0] for p in placebo_dates])
        p_val = float((plc <= stat).mean())
        beta = ols(np.log(panel[col])[est].values, design(panel, donors, est)[est].values)
        pred = np.exp(np.log(panel[col]) - ab)
        R[key] = {
            "stat_log": stat, "stat_pct": pct(stat), "p_placebo_time": p_val,
            "n_placebo": int(len(plc)), "placebo_from": str(first_placebo.date()), "placebo_to": str(last_placebo.date()),
            "placebo_p10_pct": pct(np.quantile(plc, 0.10)), "placebo_p50_pct": pct(np.quantile(plc, 0.50)), "placebo_p90_pct": pct(np.quantile(plc, 0.90)),
            "verdict": "flow was lost" if (stat < 0 and p_val < 0.10) else "no detectable loss",
            "beta": dict(zip(["const", "log_donor_index", "log_near_spot_vol", "log_zec_spot_vol"], map(float, beta))),
            "r2_est": float(1 - ab[est].var() / np.log(panel[col])[est].var()),
            "by_horizon_pct": {str(h): pct(event_stat(panel, col, donors, T, h)[0]) for h in (7, 14, 28, int((LAST_DAY - T).days) + 1)},
            "usd_actual_event_window": float(panel.loc[evt, col].sum()), "usd_predicted_event_window": float(pred[evt].sum()),
            "placebo_stats_pct": [pct(x) for x in plc],
            "series": [{"d": str(i.date()), "actual": float(panel.at[i, col]), "predicted": float(pred[i]), "abnormal_log": float(ab[i])}
                       for i in panel.index[panel.index >= EST_START]],
        }
    HACK = pd.Timestamp("2026-09-24")  # Bitget hack; the blocking followed it, before the 09-29 press reports
    R["H1"]["from_hack_date_pct"] = pct(event_stat(panel, "volume", donors, HACK)[0])  # sensitivity, not pre-registered
    R["H1"]["n_independent"] = (R["H1"]["n_placebo"] + HORIZON - 1) // HORIZON  # non-overlapping 28-day windows in the placebo span
    R["H1"]["mde_pct"] = R["H1"]["placebo_p10_pct"]  # detection threshold: a loss this size reaches p = 0.10 only about half the time
    # The donor rule exactly as written in PREREGISTRATION.md: a donor is dropped only for missing days in the estimation
    # window. The index averages donors before taking logs, so a zero-volume day does not break it. Deviation 1 dropped more.
    literal = [d for d in DONORS_PREREG if not panel[d][est].isna().any()]
    lit_stat, lit_ab = event_stat(panel, "volume", literal, T)
    lit_plc = np.array([event_stat(panel, "volume", literal, x)[0] for x in placebo_dates])
    lit_plc = lit_plc[np.isfinite(lit_plc)]
    R["H1"]["literal"] = {"donors": literal, "dropped": [d for d in DONORS_PREREG if d not in literal], "stat_pct": pct(lit_stat),
                          "p_placebo_time": float((lit_plc <= lit_stat).mean()), "n_placebo": int(len(lit_plc)),
                          "mde_pct": pct(np.quantile(lit_plc, 0.10)),
                          "verdict": "flow was lost" if (lit_stat < 0 and float((lit_plc <= lit_stat).mean()) < 0.10) else "no detectable loss",
                          "without_0x_pct": pct(event_stat(panel, "volume", [x for x in literal if x != "0x-bridge-aggregator"], T)[0]),
                          "without": {d: pct(event_stat(panel, "volume", [x for x in literal if x != d], T)[0]) for d in literal}}
    assert R["H1"]["literal"]["verdict"] == R["H1"]["verdict"], "the two donor rules give different pre-registered verdicts: say so in the thesis"
    # The decision rule in PREREGISTRATION.md, applied mechanically.
    if R["H1"]["verdict"] == "flow was lost":
        R["H1"]["prereg_outcome"] = "flow was lost"
    elif R["H1"]["mde_pct"] > -0.25:
        R["H1"]["prereg_outcome"] = "durability objection weakened"
    else:
        R["H1"]["prereg_outcome"] = "no collapse, but too imprecise to clear the 25% bar"
    # When did the fee premium appear? (not pre-registered)
    fab = pd.Series({pd.Timestamp(x["d"]): x["abnormal_log"] for x in R["H2"]["series"]})
    R["H2"]["week_before_pct"] = pct(fab[T - pd.Timedelta(days=7):T - pd.Timedelta(days=1)].mean())
    R["H2"]["after_window_pct"] = pct(fab[T + pd.Timedelta(days=HORIZON):].mean())

    # Robustness grid (not pre-registered): every combination of donor set, controls, event date and horizon.
    wide = panel.copy()
    wide["li.fi-bridge-aggregator"] = llama_series("donor_li.fi-bridge-aggregator").reindex(pd.date_range(panel.index.min(), LAST_DAY)).interpolate()
    wide["0x-bridge-aggregator"] = llama_series("donor_0x-bridge-aggregator")
    sets = {"rule set": donors, "+ 0x": donors + ["0x-bridge-aggregator"], "+ LI.FI": donors + ["li.fi-bridge-aggregator"],
            "+ 0x + LI.FI": donors + ["0x-bridge-aggregator", "li.fi-bridge-aggregator"],
            "aggregators only": [d for d in donors if d != "chainflip-amm"]}
    grid = []
    for sname, dset in sets.items():
        for controls in ("donors + spot volume", "donors only"):
            for ename, edate in (("freeze", T), ("exploit", E2)):
                for h in (14, 28, int((LAST_DAY - edate).days) + 1):
                    e_end = edate - pd.Timedelta(days=GAP + 1)
                    e_mask = (wide.index >= e_end - pd.Timedelta(days=EST_LEN - 1)) & (wide.index <= e_end)
                    v_mask = (wide.index >= edate) & (wide.index < edate + pd.Timedelta(days=h))
                    X = design(wide, dset, e_mask)
                    if controls == "donors only":
                        X = X[["const", "log_donor_index"]]
                    grid.append({"donors": sname, "controls": controls, "event": ename, "days": h,
                                 "pct": pct(abnormal(np.log(wide.volume), X, e_mask, v_mask)[0])})
    g = np.array([x["pct"] for x in grid])
    zx = wide["0x-bridge-aggregator"]
    zero_x_growth = float(zx[evt].mean() / zx[est].mean())  # event-window vs estimation-window mean daily volume
    R["grid"] = {"zero_x_growth": zero_x_growth, "specs": grid, "n": len(grid), "min_pct": float(g.min()), "median_pct": float(np.median(g)), "max_pct": float(g.max()),
                 "share_negative": float((g < 0).mean()), "share_below_mde": float((g < R["H1"]["mde_pct"]).mean()),
                 "with_0x_pct": next(x["pct"] for x in grid if x["donors"] == "+ 0x" and x["controls"] == "donors + spot volume" and x["event"] == "freeze" and x["days"] == HORIZON)}

    # synthetic control + placebo in space
    ratio, w, synth, scaled = synthetic(panel, "volume", donors, est, evt)
    space = {d: synthetic(panel, d, [x for x in donors if x != d] + ["volume"], est, evt)[0] for d in donors}
    R["synth"] = {"ratio_pct": ratio, "weights": w, "placebo_space_pct": space,
                  "rank_from_bottom": int(1 + sum(v < ratio for v in space.values())), "n_units": len(space) + 1,
                  "series": [{"d": str(i.date()), "actual": float(scaled[i]), "synthetic": float(synth[i])}
                             for i in panel.index[panel.index >= EST_START] if np.isfinite(synth[i])]}

    # take rate and plain window means
    def wmean(col, a, b):
        return float(panel.loc[a:b, col].mean())
    windows = {"estimation": (EST_START, EST_END), "between": (E0, T - pd.Timedelta(days=1)),
               "event": (T, T + pd.Timedelta(days=HORIZON - 1)), "after": (T + pd.Timedelta(days=HORIZON), LAST_DAY)}
    R["windows"] = {k: {"from": str(a.date()), "to": str(b.date()), "days": int((b - a).days + 1),
                        "volume_per_day": wmean("volume", a, b), "fees_per_day": wmean("fees", a, b), "revenue_per_day": wmean("revenue", a, b),
                        "take_rate_bps": 1e4 * panel.loc[a:b, "fees"].sum() / panel.loc[a:b, "volume"].sum(),
                        "capture_bps": 1e4 * panel.loc[a:b, "revenue"].sum() / panel.loc[a:b, "volume"].sum(),
                        "donor_index": float((panel.loc[a:b, donors] / panel.loc[est, donors].mean()).mean(axis=1).mean()),
                        "near_spot_vol_per_day": wmean("near_vol", a, b), "near_price": wmean("near_price", a, b)}
                    for k, (a, b) in windows.items()}
    R["daily"] = [{"d": str(i.date()), "volume": float(r.volume), "fees": float(r.fees), "revenue": float(r.revenue),
                   "near_price": float(r.near_price), "zec_price": float(r.zec_price)} for i, r in panel[panel.index >= EST_START].iterrows()]

    # ---- H3 / H4: balances in token units -----------------------------------------
    total, usd, chains = balances()
    base = T - pd.Timedelta(days=1)
    price0 = (usd.loc[base] / total.loc[base]).replace([np.inf, -np.inf], np.nan).dropna()  # fixed prices on T-1

    def fixed_value(units):
        cols = [c for c in units.columns if c in price0.index]
        return (units[cols].fillna(0) * price0[cols]).sum(axis=1)

    paused = sum(fixed_value(chains[c]).reindex(total.index).fillna(0) for c in PAUSED if c in chains)
    others = sum(fixed_value(v).reindex(total.index).fillna(0) for c, v in chains.items() if c not in PAUSED)
    allv = fixed_value(total)
    zec_units = total["ZEC"]
    nonzec = fixed_value(total.drop(columns=["ZEC"]))
    rest = fixed_value(total.drop(columns=["ZEC", "NEAR"]))  # neither ZEC nor NEAR (exploratory)
    near_units = total["NEAR"]
    starts = pd.date_range(EST_START, EST_END - pd.Timedelta(days=HORIZON))

    def did(days):
        a, b = base, base + pd.Timedelta(days=days)
        real = logchg(paused, a, b) - logchg(others, a, b)
        plc = placebo_changes(paused, starts, days) - placebo_changes(others, starts, days)
        return {"paused_pct": pct(logchg(paused, a, b)), "others_pct": pct(logchg(others, a, b)), "diff_pct": pct(real),
                "p_placebo": float((plc <= real).mean()), "placebo_p10_pct": pct(np.quantile(plc, 0.10)), "placebo_p90_pct": pct(np.quantile(plc, 0.90))}

    R["H3"] = {"paused_chains": [{"Binance": "BNB Chain"}.get(c, c) for c in PAUSED if c in chains], "base_day": str(base.date()),
               "paused_usd_base": float(paused[base]), "others_usd_base": float(others[base]), "all_usd_base": float(paused[base] + others[base]),
               "d14": did(14), "d28": did(28),
               "trough": {"day": str((paused / paused[base])[T:T + pd.Timedelta(days=27)].idxmin().date()),
                          "pct": float((paused / paused[base])[T:T + pd.Timedelta(days=27)].min() - 1)}}

    def zec_test(a, days):
        b = a + pd.Timedelta(days=days)
        plc_z, plc_o = placebo_changes(zec_units, starts, days), placebo_changes(nonzec, starts, days)
        z, o = logchg(zec_units, a, b), logchg(nonzec, a, b)
        return {"from": str(a.date()), "to": str(b.date()), "zec_pct": pct(z), "zec_placebo_p10_pct": pct(np.quantile(plc_z, 0.10)),
                "zec_placebo_p90_pct": pct(np.quantile(plc_z, 0.90)), "zec_p": float((plc_z <= z).mean()),
                "nonzec_pct": pct(o), "nonzec_placebo_p10_pct": pct(np.quantile(plc_o, 0.10)), "nonzec_p": float((plc_o <= o).mean()),
                "zec_beyond": bool(z < np.quantile(plc_z, 0.10)), "nonzec_beyond": bool(o < np.quantile(plc_o, 0.10))}

    a0, aT = zec_test(E0 - pd.Timedelta(days=1), 14), zec_test(base, 28)
    R["H4"] = {"after_E0_14d": a0, "after_T_28d": aT,
               "verdict": "supported" if any(t["zec_beyond"] and not t["nonzec_beyond"] for t in (a0, aT)) else "not supported",
               "zec_units_base": float(zec_units[base]), "zec_usd_base": float(zec_units[base] * price0["ZEC"]),
               "zec_share_of_balances_base": float(zec_units[base] * price0["ZEC"] / allv[base])}
    R["inventory"] = {k: {"all_usd_fixed": float(allv[d]), "near_units_vs_base": float(near_units[d] / near_units[base] - 1),
                          "rest_vs_base": float(rest[d] / rest[base] - 1), "zec_units_vs_base": float(zec_units[d] / zec_units[base] - 1)}
                      for k, d in (("est_end", EST_END), ("base", base), ("t28", base + pd.Timedelta(days=28)), ("last", LAST_DAY))}
    R["inventory"]["t28_vs_est_end"] = float(allv[base + pd.Timedelta(days=28)] / allv[EST_END] - 1)
    R["inventory"]["base_vs_est_end"] = float(allv[base] / allv[EST_END] - 1)
    bal_idx = total.index[(total.index >= EST_START) & (total.index <= LAST_DAY)]
    R["balances"] = [{"d": str(i.date()), "paused": float(paused[i] / paused[base]), "others": float(others[i] / others[base]),
                      "zec_units": float(zec_units[i] / zec_units[base]), "nonzec": float(nonzec[i] / nonzec[base]),
                      "near_units": float(near_units[i] / near_units[base]), "rest": float(rest[i] / rest[base]),
                      "all_usd_fixed": float(allv[i])} for i in bal_idx]
    R["top_balances_base"] = [{"token": k, "usd": float(v)} for k, v in (total.loc[base].reindex(price0.index).fillna(0) * price0).sort_values(ascending=False).head(8).items()]

    # ---- value at stake -------------------------------------------------------------
    last30 = panel.loc[LAST_DAY - pd.Timedelta(days=29):LAST_DAY]
    R["stake"] = {"revenue_30d": float(last30.revenue.sum()), "revenue_annualised": float(last30.revenue.sum() * 365 / 30),
                  "fees_30d": float(last30.fees.sum()), "volume_30d": float(last30.volume.sum()),
                  "fees_shortfall_event_window": R["H2"]["usd_predicted_event_window"] - R["H2"]["usd_actual_event_window"],
                  "volume_shortfall_event_window": R["H1"]["usd_predicted_event_window"] - R["H1"]["usd_actual_event_window"]}

    # Intents' share of the revenue DefiLlama tracks on NEAR over the same 30 days: every protocol on NEAR plus the chain's
    # own revenue. Off-chain lines of business (NEAR AI Cloud, for example) are not tracked there, so they are not in it.
    rev = {}
    for t, by in raw("near_protocols_revenue")["totalDataChartBreakdown"]:
        if last30.index[0] <= pd.Timestamp(t, unit="s").normalize() <= LAST_DAY:
            for k, v in by.items():
                rev[k] = rev.get(k, 0.0) + float(v)
    chain_rev = float(llama_series("near_chain_revenue")[last30.index[0]:LAST_DAY].sum())
    tracked = sum(rev.values()) + chain_rev
    R["revenue_mix"] = {"intents": rev["NEAR Intents"], "chain": chain_rev, "tracked": tracked,
                        "intents_share": rev["NEAR Intents"] / tracked, "intents_vs_chain": rev["NEAR Intents"] / chain_rev,
                        "protocols": len(rev), "from": str(last30.index[0].date()), "to": str(LAST_DAY.date())}

    mcap = float(near.mcap[LAST_DAY])
    R["stake"].update({"near_mcap": mcap, "mcap_to_revenue": mcap / R["stake"]["revenue_annualised"],
                       "revenue_at_mde": -R["H1"]["mde_pct"] * R["stake"]["revenue_annualised"]})

    # ---- Rivals (exploratory, added after the pre-registration): raw 28-day volume change at T ----------
    # Every fetched comparison venue with positive volume on all 56 days around the date; no model.
    rivals_all = {n: llama_series("donor_" + n) for n in DONORS_PREREG}

    def raw_chg(x, t):
        a, b = x[t:t + pd.Timedelta(days=HORIZON - 1)], x[t - pd.Timedelta(days=HORIZON):t - pd.Timedelta(days=1)]
        if len(a) < HORIZON or len(b) < HORIZON or (a <= 0).any() or (b <= 0).any():
            return np.nan
        return float(np.log(a.mean() / b.mean()))

    def vs_rivals(t):
        r = {n: raw_chg(v, t) for n, v in rivals_all.items()}
        r = {n: x for n, x in r.items() if np.isfinite(x)}
        return raw_chg(panel["volume"], t) - float(np.median(list(r.values()))), r

    rel, rv = vs_rivals(T)
    rel_plc = np.array([vs_rivals(t)[0] for t in placebo_dates])
    R["rivals"] = {"intents_pct": pct(raw_chg(panel["volume"], T)), "by_venue_pct": {n: pct(x) for n, x in rv.items()},
                   "median_pct": pct(float(np.median(list(rv.values())))), "n": len(rv),
                   "n_beaten": int(sum(x < raw_chg(panel["volume"], T) for x in rv.values())),
                   "relative_log": rel, "p": float((rel_plc >= rel).mean()), "placebo_p50_log": float(np.median(rel_plc))}
    # The same comparison against August, before the September rally (rivals rallied much harder).
    pre_rally, evt_days = slice("2026-08-01", "2026-08-28"), slice(T, T + pd.Timedelta(days=HORIZON - 1))
    vs_aug = lambda x: float(x[evt_days].mean() / x[pre_rally].mean() - 1)
    R["rivals"]["vs_august"] = {"intents_pct": vs_aug(panel["volume"]), "median_pct": float(np.median([vs_aug(rivals_all[n]) for n in rv]))}

    # ---- H5 (exploratory): accounts that sign their own intents.near transactions -------------
    # Relayed 1Click swaps are signed by intents.near itself, so they are excluded; what is left is
    # self-custody users, solvers and escrow contracts.
    sg = pd.read_csv(os.path.join(RAW, "bq_intents_signers_daily.csv"), parse_dates=["block_date"])
    relayed_share = float(sg.loc[sg.signer_account_id == "intents.near", "n"].sum() / sg.n.sum())
    sg = sg[sg.signer_account_id != "intents.near"]
    by_day = {d: set(g.signer_account_id) for d, g in sg.groupby("block_date")}
    days = pd.date_range(sg.block_date.min(), LAST_DAY)
    active = pd.Series({d: len(by_day.get(d, ())) for d in days})

    def seen(a, b):
        return set().union(*(by_day.get(d, set()) for d in pd.date_range(a, b)))

    def resight(t, min_days=1):
        """Share of accounts active on at least min_days of the 28 days before t that are active in the 28 days from t."""
        days_before = pd.Series([a for d in pd.date_range(t - pd.Timedelta(days=HORIZON), t - pd.Timedelta(days=1))
                                 for a in by_day.get(d, ())]).value_counts()
        before = set(days_before[days_before >= min_days].index)
        return len(before & seen(t, t + pd.Timedelta(days=HORIZON - 1))) / len(before), len(before)

    def active_change(t):
        return float(np.log(active[t:t + pd.Timedelta(days=HORIZON - 1)].mean() / active[t - pd.Timedelta(days=HORIZON):t - pd.Timedelta(days=1)].mean()))

    h5_placebo = pd.date_range(days.min() + pd.Timedelta(days=HORIZON), E0 - pd.Timedelta(days=HORIZON))
    first_seen = sg.groupby("signer_account_id").block_date.min()

    def cohort(t, returning):
        days_before = pd.date_range(t - pd.Timedelta(days=HORIZON), t - pd.Timedelta(days=1))
        acc = set().union(*(by_day.get(d, set()) for d in days_before))
        acc = {a for a in acc if (first_seen[a] < days_before[0]) == returning}
        return len(acc & seen(t, t + pd.Timedelta(days=HORIZON - 1))) / len(acc) if acc else np.nan, len(acc)

    cohorts = {}
    for name, returning in (("new", False), ("returning", True)):  # added after seeing the tiers
        (rate, n), plc = cohort(T, returning), np.array([cohort(t, returning)[0] for t in h5_placebo])
        plc = plc[np.isfinite(plc)]
        cohorts[name] = {"n": n, "rate": rate, "p": float((plc <= rate).mean()), "placebo_p50": float(np.median(plc))}
    tiers = {}
    for k in (1, 2, 5):  # 1 is the pre-registered rate; 2 and 5 (repeat and heavy users) were added after seeing it
        (rate, n), plc = resight(T, k), np.array([resight(t, k)[0] for t in h5_placebo])
        tiers[str(k)] = {"n": n, "rate": rate, "p": float((plc <= rate).mean()), "placebo_p10": float(np.quantile(plc, 0.10)),
                         "placebo_p50": float(np.quantile(plc, 0.50))}
    ac, ac_plc = active_change(T), np.array([active_change(t) for t in h5_placebo])
    evt_tx = sg[(sg.block_date >= T) & (sg.block_date < T + pd.Timedelta(days=HORIZON))].groupby("signer_account_id").n.sum()
    R["H5"] = {"from": str(days.min().date()), "relayed_share": relayed_share, "n_accounts": int(sg.signer_account_id.nunique()),
               "active_per_day_median": float(active.median()), "n_placebo": int(len(h5_placebo)), "n_independent": (len(h5_placebo) + HORIZON - 1) // HORIZON,
               "resight": tiers, "cohorts": cohorts,
               "active_change_pct": pct(ac), "active_change_p": float((ac_plc <= ac).mean()),
               "active_change_placebo_p10_pct": pct(np.quantile(ac_plc, 0.10)),
               "top10_share_event": float(evt_tx.sort_values(ascending=False).head(10).sum() / evt_tx.sum()),
               "daily": [{"d": str(d.date()), "active": int(v)} for d, v in active.items()]}

    # ---- Onchain cross-check of H1 (added after the pre-registration) ------------------------------
    # Same model and window, with onchain transaction counts (BigQuery) as the outcome instead of DefiLlama
    # volume. BigQuery data starts 2026-03-01, so the calm windows available fall in the summer uptrend.
    sg_all = pd.read_csv(os.path.join(RAW, "bq_intents_signers_daily.csv"), parse_dates=["block_date"])
    short = panel[panel.index >= sg_all.block_date.min()].copy()
    short["tx_relayed"] = sg_all[sg_all.signer_account_id == "intents.near"].groupby("block_date").n.sum()
    short_plc = pd.date_range(short.index.min() + pd.Timedelta(days=EST_LEN + GAP), E0 - pd.Timedelta(days=HORIZON))
    R["onchain_check"] = {"from": str(short.index.min().date()), "n_placebo": int(len(short_plc))}
    for col in ("volume", "tx_relayed"):
        st = event_stat(short, col, donors, T)[0]
        plc = np.array([event_stat(short, col, donors, t)[0] for t in short_plc])
        R["onchain_check"][col] = {"pct": pct(st), "p": float((plc <= st).mean()),
                                   "placebo_min_pct": pct(plc.min()), "placebo_max_pct": pct(plc.max())}
    usd_per_tx = (short.volume / sg_all.groupby("block_date").n.sum()).resample("MS").mean()
    R["onchain_check"]["usd_per_tx_aug"] = float(usd_per_tx["2026-08-01"])
    R["onchain_check"]["usd_per_tx_sep"] = float(usd_per_tx["2026-09-01"])

    # ---- Public visibility of Intents swaps (exploratory, added after the pre-registration) --------
    # Public onchain swap volume: the stablecoin leg of every dip4 token_diff event (BigQuery). Its ratio to
    # DefiLlama's total Intents volume falls when flow moves to execution that is not logged as public swaps
    # (Confidential Intents, generally available to every app from 2026-07-08).
    sv = pd.read_csv(os.path.join(RAW, "bq_intents_stable_volume_daily.csv"), parse_dates=["block_date"])
    # One-sided: a stablecoin-to-stablecoin swap shows a positive stablecoin amount in both parties' diffs, so half of
    # that part is removed. The gross figure (both legs) is kept for comparison.
    sv_day = sv.groupby("block_date")[["usd", "usd_stable_to_stable"]].sum()
    public_gross = sv_day.usd
    public = sv_day.usd - sv_day.usd_stable_to_stable / 2
    GA = pd.Timestamp("2026-07-08")

    def share(a, b):
        return float(public[a:b].sum() / panel["volume"][a:b].sum())

    def share_chg(t):
        return float(np.log(share(t, t + pd.Timedelta(days=HORIZON - 1)) / share(t - pd.Timedelta(days=HORIZON), t - pd.Timedelta(days=1))))

    priv_plc = pd.date_range(public.index.min() + pd.Timedelta(days=HORIZON), E0 - pd.Timedelta(days=HORIZON))
    plc = np.array([share_chg(t) for t in priv_plc])
    day = pd.Timedelta(days=1)
    R["privacy_gross"] = {"after_ga": float(public_gross[GA:EST_END].sum() / panel["volume"][GA:EST_END].sum()),
                          "stable_to_stable_share": float(sv_day.usd_stable_to_stable[GA:LAST_DAY].sum() / sv_day.usd[GA:LAST_DAY].sum())}
    R["privacy"] = {
        "ga_date": str(GA.date()), "n_placebo": int(len(plc)), "placebo_from": str(priv_plc[0].date()),
        "placebo_p50_pct": pct(np.median(plc)), "placebo_min_pct": pct(plc.min()),
        "windows": {k: share(a, b) for k, (a, b) in {
            "before_ga": (EST_START, GA - day), "after_ga": (GA, E0 - day), "between": (E0, T - day),
            "event": (T, T + pd.Timedelta(days=HORIZON - 1)), "after": (T + pd.Timedelta(days=HORIZON), LAST_DAY)}.items()},
        "chg": {k: {"pct": pct(share_chg(t)), "p": float((plc <= share_chg(t)).mean())}
                for k, t in {"freeze": T, "forum": E0, "ga": GA}.items()},
        "daily": [{"d": str(d.date()), "share": float(v)} for d, v in
                  (public.rolling(7).sum() / panel["volume"].reindex(public.index).rolling(7).sum()).dropna()[EST_START:].items()],
    }
    w = R["privacy"]["windows"]
    R["privacy"]["visible_event_vs_summer"] = w["event"] / w["after_ga"]
    R["privacy"]["visible_after_vs_summer"] = w["after"] / w["after_ga"]
    # Onchain only, no DefiLlama: every event intents.near logs, by name and format version, plus code deploys.
    ecl = pd.read_csv(os.path.join(RAW, "bq_intents_event_counts_daily.csv"), parse_dates=["block_date"])
    ec = ecl.pivot_table(index="block_date", columns="event", values="n", aggfunc="sum").fillna(0)
    deploys = pd.read_csv(os.path.join(RAW, "bq_intents_deploys.csv"), parse_dates=["block_date"]).block_date
    v_new = ecl[(ecl.event == "token_diff") & ~ecl.version.str.startswith("0.3")].block_date.min()
    ec_win = {"before": (ec.index.min(), E0 - day), "between": (E0, T - day), "after_upgrade": (deploys.max() + day, T + pd.Timedelta(days=HORIZON - 1)),
              "after": (T + pd.Timedelta(days=HORIZON), LAST_DAY)}
    deposit_change = float(ec.loc[ec_win["after"][0]:ec_win["after"][1], "mt_mint"].mean() / ec.loc[ec_win["before"][0]:ec_win["before"][1], "mt_mint"].mean() - 1)
    R["privacy"]["events"] = {"deposit_change_pct": deposit_change,
        "from": str(ec.index.min().date()), "deploys": [str(d.date()) for d in deploys], "new_format_from": str(v_new.date()),
        "windows": {k: {"from": str(a.date()), "to": str(b.date()), **{c: float(ec.loc[a:b, c].mean()) for c in ("token_diff", "intents_executed", "transfer", "mt_mint")}}
                    for k, (a, b) in ec_win.items()},
        "daily": [{"d": str(d.date()), "swaps": float(r.token_diff), "executed": float(r.intents_executed), "transfers": float(r.transfer)}
                  for d, r in ec[["token_diff", "intents_executed", "transfer"]].rolling(7).mean().dropna().iterrows()],
    }
    # H1 on public onchain volume (same pre-registered design, outcome swapped)
    on = panel.copy()
    on["public"] = public
    st = event_stat(on, "public", donors, T)[0]
    on_plc = np.array([event_stat(on, "public", donors, t)[0] for t in placebo_dates])
    R["privacy"]["n_lower"] = int((plc < share_chg(T)).sum())
    R["privacy"]["n_independent"] = len(priv_plc) // (2 * HORIZON) + 1  # non-overlapping 56-day before/after pairs
    R["privacy"]["h1_public_pct"] = pct(st)
    R["privacy"]["h1_public_p"] = float((on_plc <= st).mean())

    # ---- Where the public swaps went: Confidential Intents (added after seeing results) ------------
    # NEAR Intents' changelog, 2026-10-27: "From October 27, 2026, 1Click swaps settle confidentially": the swap
    # settles on the NEAR Private Shard (FAR), and only the shield and unshield are on the public chain, as transfers
    # to and from the Treasury account. The switch date comes from the changelog, not from this data.
    SWITCH, TREASURY = pd.Timestamp("2026-10-27"), "51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe"
    cd = pd.read_csv(os.path.join(RAW, "bq_intents_confidential_daily.csv"), parse_dates=["block_date"]).set_index("block_date")
    c_win = {"august": (pd.Timestamp("2026-08-01"), pd.Timestamp("2026-08-31")), "before": (E0, SWITCH - day),
             "after": (SWITCH + day, LAST_DAY)}
    # Swap-level trace: a seeded random sample of 300 successful 1Click swaps on each sampled day (Explorer API),
    # each followed through its NEAR transactions (BigQuery) to what intents.near logged.
    with open(os.path.join(RAW, "explorer_trace_sample.json")) as f:
        sample = json.load(f)
    tr = pd.read_csv(os.path.join(RAW, "bq_intents_swap_trace.csv")).set_index("tx_hash")
    trace = {}
    for d, s in sample.items():
        sw = pd.DataFrame([{"public": any(tr.token_diff.get(h, 0) > 0 for h in hashes),
                            "treasury": any(tr.treasury.get(h, 0) > 0 for h in hashes),
                            "found": any(h in tr.index for h in hashes),
                            "n_hashes": len(hashes)} for hashes in s["near_tx_hashes"]])
        # The dollar-weighted shares and the deposit type are computed when the sample is pulled (src/fetch_explorer.py):
        # the swaps' amounts are not stored.
        trace[d] = {"n": len(sw), "swaps_that_day": s["swaps_that_day"], "found": float(sw.found.mean()),
                    "public": float(sw.public.mean()), "public_usd": s["public_usd"],
                    "treasury": float(sw.treasury.mean()), "treasury_usd": s["treasury_usd"],
                    "hashes_median": float(sw.n_hashes.median()), "deposit_confidential": s["deposit_confidential"]}
    # 1Click volume from the Explorer API: successful swaps of $100 or more (about 99% of 1Click dollars), by day.
    ex = pd.read_csv(os.path.join(RAW, "explorer_1click_daily.csv"), parse_dates=["day"]).groupby("day")[["swaps", "usd_in"]].sum()
    ex_win = {k: float(ex.usd_in[a:b].mean()) for k, (a, b) in {**c_win, "event": (T, T + pd.Timedelta(days=HORIZON - 1))}.items()}
    roll = lambda s: s.rolling(7).mean().dropna()
    R["confidential"] = {
        "switch_date": str(SWITCH.date()), "treasury": TREASURY, "trace": trace,
        "windows": {k: {"from": str(a.date()), "to": str(b.date()),
                        "public_swaps": float(cd.with_token_diff[a:b].mean()), "treasury": float(cd.with_treasury[a:b].mean()),
                        "oneclick_usd": ex_win[k], "public_usd": float(public[a:b].mean()), "defillama_usd": float(panel["volume"][a:b].mean())}
                    for k, (a, b) in c_win.items()},
        "oneclick_event_vs_august": ex_win["event"] / ex_win["august"] - 1,
        "oneclick_after_vs_august": ex_win["after"] / ex_win["august"] - 1,
        "daily": [{"d": str(d.date()), "public": float(r.with_token_diff), "treasury": float(r.with_treasury)}
                  for d, r in roll(cd[["with_token_diff", "with_treasury"]]).iterrows()],
        "volume_daily": [{"d": str(d.date()), "oneclick": float(v), "public": float(public.rolling(7).mean().get(d, np.nan)),
                          "defillama": float(panel["volume"].rolling(7).mean().get(d, np.nan))} for d, v in roll(ex.usd_in).items()],
    }

    # ---- who routes the flow (added after the pre-registration) ---------------------------
    # Successful 1Click swaps of $10,000 or more (Explorer API), summed by day and integrating app (referral). Swaps with
    # no referral are kept as their own group, not as an integrator. The counts of sender addresses that came back are
    # computed when the data is pulled (src/fetch_explorer.py): no per-swap record or address is stored.
    lg = pd.read_csv(os.path.join(RAW, "explorer_large_daily.csv"), parse_dates=["day"], keep_default_na=False)
    with open(os.path.join(RAW, "explorer_large_senders.json")) as f:
        snd = json.load(f)
    assert (snd["freeze"], snd["horizon"]) == (str(T.date()), HORIZON), "explorer_large_senders.json was computed for another event window"
    l_win = {"august": c_win["august"], "before": (E0, T - day), "event": (T, T + pd.Timedelta(days=HORIZON - 1)), "after": c_win["after"]}
    named = lg[lg.referral != ""]
    rank = named.groupby("referral").usd_in.sum().sort_values(ascending=False)
    top1, next4 = rank.index[0], list(rank.index[1:5])
    aug_big = named[named.day <= l_win["august"][1]].groupby("referral").usd_in.sum()
    aug_big_usd = aug_big[aug_big >= 1e6] / 31  # dollars a day in August, for the integrators that routed $1M or more
    aug_big = set(aug_big_usd.index)

    FALLER = "new.intents-referral.near"  # the one label behind most of the fall; its volume dropped before the freeze

    def l_stats(a, b):
        w, n = lg[(lg.day >= a) & (lg.day <= b)], (b - a).days + 1
        by = w[w.referral != ""].groupby("referral").usd_in.sum().sort_values(ascending=False)
        return {"from": str(a.date()), "to": str(b.date()), "swaps_per_day": float(w.swaps.sum() / n), "usd_per_day": float(w.usd_in.sum() / n),
                "share_of_oneclick": float(w.usd_in.sum() / ex.usd_in[a:b].sum()), "integrators": int(by.size),
                "top1_share": float(by.get(top1, 0) / w.usd_in.sum()), "top5_share": float(by.iloc[:5].sum() / w.usd_in.sum()),
                "no_referral_share": float(w.usd_in[w.referral == ""].sum() / w.usd_in.sum()),
                "august_big_still_routing": int(len(aug_big & set(by.index))),
                "august_big_kept_half": int((by.reindex(aug_big_usd.index).fillna(0) / n >= 0.5 * aug_big_usd).sum()),
                "august_big_at_or_above": int((by.reindex(aug_big_usd.index).fillna(0) / n >= aug_big_usd).sum()),
                "august_big_usd_ratio": float(by.reindex(aug_big_usd.index).fillna(0).sum() / n / aug_big_usd.sum()),
                "august_big_usd_ratio_ex_faller": float(by.reindex(aug_big_usd.index.drop(FALLER)).fillna(0).sum() / n / aug_big_usd.drop(FALLER).sum()),
                "by_integrator": {r: float(by.get(r, 0) / n) for r in [top1] + next4}}

    grp = lambda r: "top1" if r == top1 else "next4" if r in next4 else "rest"
    lg_daily = lg.assign(g=lg.referral.map(grp)).pivot_table(index="day", columns="g", values="usd_in", aggfunc="sum").fillna(0)
    R["large"] = {
        "min_usd": 10000, "n": int(lg.swaps.sum()), "from": str(lg.day.min().date()), "top1": top1, "next4": next4,
        "august_big": len(aug_big), "sender_known": snd["sender_known"],
        "windows": {k: l_stats(a, b) for k, (a, b) in l_win.items()},
        "usd_event_vs_august": None, "usd_after_vs_august": None,
        "senders": snd["senders"], "calm_dates": snd["calm_dates"], "calm_from": snd["calm_from"], "calm_to": snd["calm_to"],
        "daily": [{"d": str(d.date()), "top1": float(r.top1), "next4": float(r.next4), "rest": float(r.rest)} for d, r in roll(lg_daily).iterrows()],
    }
    lw = R["large"]["windows"]
    R["large"]["by"] = [{k: lw[k]["by_integrator"][r] for k in l_win} for r in [top1] + next4] + \
                       [{k: lw[k]["no_referral_share"] * lw[k]["usd_per_day"] for k in l_win}]
    R["large"]["usd_event_vs_august"] = lw["event"]["usd_per_day"] / lw["august"]["usd_per_day"] - 1
    R["large"]["usd_after_vs_august"] = lw["after"]["usd_per_day"] / lw["august"]["usd_per_day"] - 1

    # ---- long-term view (added after the pre-registration) ------------------------------
    vol_all, rev_all = llama_series("intents_volume"), llama_series("intents_revenue")
    month_end = LAST_DAY.to_period("M").start_time  # first day of the current, incomplete month
    monthly = pd.DataFrame({"volume": vol_all.resample("MS").sum(), "revenue": rev_all.resample("MS").sum()})
    monthly = monthly[monthly.index < month_end]
    chain_supply = pd.read_csv(os.path.join(RAW, "bq_circulating_supply.csv"), parse_dates=["block_date"]).set_index("block_date") / 1e24
    supply = chain_supply.total_tokens_supply  # NEAR's own supply table (BigQuery): issuance net of burns
    s1 = min(LAST_DAY, supply.index.max())  # supply needs BigQuery; scoring predictions later does not
    s0 = s1 - pd.Timedelta(days=365)
    supply_growth_yr = float(supply[s1] - supply[s0])
    last_m = monthly.index.max()
    R["long_term"] = {
        "monthly": [{"m": str(i.date())[:7], "volume": float(r.volume), "revenue": None if pd.isna(r.revenue) else float(r.revenue)}
                    for i, r in monthly.iterrows()],  # revenue is not reported before DefiLlama began tracking it
        "first_month": str(monthly.index[monthly.volume > 0].min().date())[:7],
        "last_month": str(last_m.date())[:7], "last_month_volume": float(monthly.volume[last_m]),
        "volume_yoy": float(monthly.volume[last_m] / monthly.volume[last_m - pd.DateOffset(years=1)]),
        "record_month": str(monthly.volume.idxmax().date())[:7], "record_volume": float(monthly.volume.max()),
        "plateau_min": float(monthly.volume[monthly.volume.idxmax() - pd.DateOffset(months=9):monthly.volume.idxmax() - pd.DateOffset(months=1)].min()),
        "plateau_max": float(monthly.volume[monthly.volume.idxmax() - pd.DateOffset(months=9):monthly.volume.idxmax() - pd.DateOffset(months=1)].max()),
        "supply_from": str(s0.date()), "supply_to": str(s1.date()), "supply_now": float(supply[s1]),
        "supply_growth_yr": supply_growth_yr, "supply_growth_pct_yr": supply_growth_yr / float(supply[s0]),
        "circulating_growth_yr": float(chain_supply.circulating_tokens_supply[s1] - chain_supply.circulating_tokens_supply[s0]),
    }
    first_peak = monthly.volume[:monthly.volume.idxmax() - pd.DateOffset(months=9)].idxmax()  # the first surge's peak
    capture_now = R["stake"]["revenue_30d"] / R["stake"]["volume_30d"] * 1e4
    R["long_term"].update({
        "first_peak_month": str(first_peak.date())[:7], "first_peak_volume": float(monthly.volume[first_peak]),
        "last_vs_first_peak": float(monthly.volume[last_m] / monthly.volume[first_peak]),
        "capture_now_bps": capture_now,
    })

    # ---- measured buybacks (added after the pre-registration) -----------------------------
    # DefiLlama's revenue is NEAR swept into three wallets (its adapter credits NEAR's Dune query 6740088) and is
    # labelled a buyback that is not burned. So the holder-side number can be read from the wallets' balances.
    wl = pd.read_csv(os.path.join(RAW, "bq_revenue_wallets_daily.csv"), parse_dates=["epoch_date"])
    wl["near"] = wl[["liquid", "unstaked_not_liquid", "staked", "reward"]].sum(axis=1)
    wallets = wl.pivot(index="epoch_date", columns="account_id", values="near")
    wallets = wallets.reindex(pd.date_range(wallets.index.min(), wallets.index.max())).ffill().fillna(0)
    held = wallets.sum(axis=1)
    w1 = min(LAST_DAY, held.index.max())
    w0, w90 = w1 - pd.Timedelta(days=HORIZON), w1 - pd.Timedelta(days=90)
    flow = held.diff().dropna()
    issued_day = supply_growth_yr / 365
    in28, in90, in_prev90 = float(held[w1] - held[w0]) / HORIZON, float(held[w1] - held[w90]) / 90, float(held[w90] - held[w90 - pd.Timedelta(days=90)]) / 90
    rev_near28 = float((rev_all / near.price)[w0 + day:w1].sum()) / HORIZON  # DefiLlama revenue, in NEAR at each day's price
    R["buyback"] = {
        "wallets": {a: float(wallets[a][w1]) for a in wallets.columns}, "as_of": str(w1.date()), "from": str(w0.date()),
        "held": float(held[w1]), "held_share_of_supply": float(held[w1] / supply[s1]),
        "staked": float(wl[["unstaked_not_liquid", "staked", "reward"]].sum().sum()),
        "outflow_days": int((flow < -1).sum()), "outflow_near": float(-flow[flow < -1].sum()), "days": int(len(flow)),
        "in_28d_per_day": in28, "issued_per_day": issued_day, "coverage_28d": in28 / issued_day, "coverage_90d": in90 / issued_day,
        "growth_needed": issued_day / in28, "in_90d_vs_prior_90d": in90 / in_prev90,
        "defillama_revenue_near_28d_per_day": rev_near28, "wallets_vs_defillama": in28 / rev_near28,
        "years_to_cover": {str(g): float(np.log(issued_day / in28) / np.log(1 + g / 100)) for g in (50, 100, 200)},
        "daily": [{"d": str(d.date()), "held": float(v)} for d, v in held[held > 0][:w1].items()],
    }
    # Buy pressure, over the same 28 days: the buyback in dollars against NEAR's daily trading volume (CoinGecko) and
    # against new supply in dollars. And NEAR's gas burn: DefiLlama's revenue for the NEAR chain is the 70% of every
    # gas fee that is burned, so it bounds what Intents' own transactions burn. The supply table above is already net
    # of burns, so the burn is inside issued_day, not in addition to it.
    win = slice(w0 + day, w1)
    px28 = float(near.price[win].mean())
    burn_near = float((llama_series("near_chain_revenue") / near.price)[win].mean())
    R["pressure"] = {"price": px28, "buyback_usd_per_day": in28 * px28, "issued_usd_per_day": issued_day * px28,
                     "spot_volume_usd_per_day": float(near.volume[win].mean()),
                     "buyback_vs_volume": in28 * px28 / float(near.volume[win].mean()),
                     "issued_vs_buyback": issued_day / in28,
                     "chain_burn_near_per_day": burn_near, "chain_burn_share_of_issuance": burn_near / issued_day}
    # The front-end fund is DefiLlama's "Front-end Affiliate Revenue" wallet; the other two are the 1Click fund and the
    # buybacks wallet, which pass NEAR between themselves, so they are counted together.
    FRONT = "fefundsadmin.sputnik-dao.near"
    core = wallets.drop(columns=FRONT).sum(axis=1)
    # Monthly inflow, full calendar months from the first one after the buyback began (2026-02-23).
    m_end = held.resample("ME").last()
    m_in = pd.DataFrame({"all": m_end.diff(), "core": core.resample("ME").last().diff()})
    m_in = m_in[(m_in.index >= "2026-03-01") & (m_in.index <= w1)].div(m_in.index.days_in_month[(m_in.index >= "2026-03-01") & (m_in.index <= w1)], axis=0)
    m_first, m_last = m_in.index[0], m_in.index[-1]
    rev_m = rev_all.resample("ME").sum()
    R["buyback"].update({
        "front_end_wallet": FRONT, "held_core": float(core[w1]), "held_front_end": float(wallets[FRONT][w1]),
        "in_28d_per_day_core": float(core[w1] - core[w0]) / HORIZON,
        "coverage_28d_core": float(core[w1] - core[w0]) / HORIZON / issued_day,
        "front_end_share_28d": 1 - float(core[w1] - core[w0]) / float(held[w1] - held[w0]),
        "monthly": [{"m": str(i.date())[:7], "per_day": float(r["all"]), "per_day_core": float(r["core"]), "coverage": float(r["all"] / issued_day)}
                    for i, r in m_in.iterrows()],
        "first_month": str(m_first.date())[:7], "last_month": str(m_last.date())[:7],
        "monthly_text": ", ".join(f"{i.strftime('%b')} {r['all']:,.0f} ({100 * r['all'] / issued_day:.0f}%)" for i, r in m_in.iterrows()),
        "last_vs_first_month": float(m_in["all"][m_last] / m_in["all"][m_first]),
        "last_vs_best_month": float(m_in["all"][m_last] / m_in["all"].max()), "best_month": str(m_in["all"].idxmax().date())[:7],
        "best_month_per_day": float(m_in["all"].max()),
        "usd_last_vs_first_month": float(rev_m[m_last] / rev_m[m_first]),
        "price_last_vs_first_month": float(near.price[m_last.replace(day=1):m_last].mean() / near.price[m_first.replace(day=1):m_first].mean()),
    })
    # Pace test (added 2026-11-11, not timestamped): the yearly growth in NEAR inflow that covers issuance by the end of 2029,
    # against the growth from the first full month of buybacks to the last, annualised.
    BY = pd.Timestamp("2029-12-31")
    bb = R["buyback"]
    bb.update({
        "cover_by": str(BY.date()), "pace_needed_yr": float(bb["growth_needed"] ** (365 / (BY - w1).days) - 1),
        "growth_needed_calm_capture": bb["growth_needed"] * capture_now / R["windows"]["estimation"]["capture_bps"],
        "growth_needed_calm_price": bb["growth_needed"] * R["windows"]["estimation"]["near_price"] / float(near.price[LAST_DAY]),
    })
    bb.update({"last3_vs_first3": float(m_in["all"][-3:].mean() / m_in["all"][:3].mean()), "last3_per_day": float(m_in["all"][-3:].mean()),
               "last_vs_low_month": float(m_in["all"][m_last] / m_in["all"].min()), "low_month": str(m_in["all"].idxmin().date())[:7],
               "n_months": int(len(m_in))})
    # ---- how much of the reported volume an outsider can count (added after the pre-registration) ----
    # DefiLlama's Intents volume is NEAR's own dataset on Dune (dune.near.dataset_near_intents_metrics), not a chain read.
    # Countable from outside: public swaps with a stablecoin side (BigQuery), plus, after the switch, the 1Click swaps
    # that settle confidentially (Explorer volume times the share of sampled dollars routed through the Treasury).
    cw, conf_usd_share = R["confidential"]["windows"], R["confidential"]["trace"]["2026-11-05"]["treasury_usd"]
    # DefiLlama's figure against twice the one-sided public count: about 1 if the reported figure counts both sides of a swap.
    two_sided = lambda a, b: float(panel["volume"][a:b].sum() / (2 * public[a:b].sum()))
    R["confidential"]["reported_vs_two_sided"] = {"summer": two_sided(GA, EST_END), "august": two_sided(*c_win["august"]),
                                                   "before": two_sided(E0, T - day)}
    R["confidential"]["countable"] = {
        "before": cw["before"]["public_usd"] / cw["before"]["defillama_usd"],
        "after_public": cw["after"]["public_usd"] / cw["after"]["defillama_usd"],
        "after": (cw["after"]["public_usd"] + conf_usd_share * cw["after"]["oneclick_usd"]) / cw["after"]["defillama_usd"],
        "august": cw["august"]["public_usd"] / cw["august"]["defillama_usd"],
        "defillama_after_vs_august": cw["after"]["defillama_usd"] / cw["august"]["defillama_usd"] - 1,
    }

    # ---- tripwires: the same measures on the latest 28 days, with the limits fixed by the calm period ----
    ab = pd.Series({pd.Timestamp(x["d"]): x["abnormal_log"] for x in R["H1"]["series"]})
    recent = LAST_DAY - pd.Timedelta(days=HORIZON - 1)
    zec28 = logchg(zec_units, LAST_DAY - pd.Timedelta(days=HORIZON), LAST_DAY)  # same span as the placebo limit
    zec_limit = float(np.quantile(placebo_changes(zec_units, starts, HORIZON), 0.10))
    take_now = 1e4 * panel.loc[recent:, "fees"].sum() / panel.loc[recent:, "volume"].sum()
    R["tripwires"] = [
        {"name": "Order flow against the model", "value": pct(ab[recent:].mean()), "limit": R["H1"]["mde_pct"], "unit": "pct",
         "rule": "28-day abnormal volume stays above the worst tenth of calm-period windows"},
        {"name": "Take rate", "value": float(take_now), "limit": R["windows"]["estimation"]["take_rate_bps"], "unit": "bps",
         "rule": "fees per dollar of volume stay above the calm-period average"},
        {"name": "Zcash held on Intents", "value": pct(zec28), "limit": pct(zec_limit), "unit": "pct",
         "rule": "28-day change in ZEC units stays above the worst tenth of calm-period windows"},
    ]
    for t in R["tripwires"]:
        t["status"] = "holding" if t["value"] >= t["limit"] else "broken"
    # How often would two of the three have been broken at once in the calm period? Same limits, each 28-day window
    # that starts in the estimation window (the windows overlap, so this is a rate over about three independent windows).
    def n_broken_at(d):
        w = slice(d, d + pd.Timedelta(days=HORIZON - 1))
        take = 1e4 * panel.loc[w, "fees"].sum() / panel.loc[w, "volume"].sum()
        return int(pct(ab[w].mean()) < R["H1"]["mde_pct"]) + int(take < R["windows"]["estimation"]["take_rate_bps"]) + \
            int(pct(logchg(zec_units, d, d + pd.Timedelta(days=HORIZON))) < pct(zec_limit))
    calm_n = np.array([n_broken_at(d) for d in starts])
    R["tripwire_calm"] = {"windows": int(len(calm_n)), "one_or_more": float((calm_n >= 1).mean()), "two_or_more": float((calm_n >= 2).mean()),
                          "independent": int(len(calm_n) + HORIZON - 1) // HORIZON}
    # The same order-flow tripwire with the donors as pre-registered (reported beside the frozen one, which archive/PREDICTIONS-2026-11-10.md fixes).
    R["tripwires"][0]["value_literal"] = pct(lit_ab[recent:].mean())
    R["tripwires"][0]["limit_literal"] = R["H1"]["literal"]["mde_pct"]
    R["tripwires"][0]["margin_literal"] = R["tripwires"][0]["value_literal"] - R["tripwires"][0]["limit_literal"]
    R["tripwires"][0]["status_literal"] = "holding" if R["tripwires"][0]["value_literal"] >= R["tripwires"][0]["limit_literal"] else "broken"
    # ---- archive/PREDICTIONS-2026-11-10.md, scored with the literal thresholds written there (frozen, not recomputed) ----
    P_FROM, P_TO = pd.Timestamp("2026-12-08"), pd.Timestamp("2027-03-31")
    ends = pd.date_range(P_FROM, min(P_TO, LAST_DAY))

    def window(e):
        return slice(e - pd.Timedelta(days=HORIZON - 1), e)

    assert all(ab[window(e)].notna().sum() == HORIZON for e in ends), "a prediction window has missing days"
    p1 = [pct(ab[window(e)].mean()) > -0.295 and pct(lit_ab[window(e)].mean()) > -0.357 for e in ends]  # both donor sets (RATING.md)
    p3 = [1e4 * panel.loc[window(e), "fees"].sum() / panel.loc[window(e), "volume"].sum() > 13.6 for e in ends]
    months = panel["volume"].resample("MS").sum()
    done = [m for m in months.index if pd.Timestamp("2026-12-01") <= m <= pd.Timestamp("2027-03-01") and m + pd.offsets.MonthEnd(0) <= LAST_DAY]
    record = any(months[m] > months[pd.Timestamp("2026-09-01")] for m in done)  # "above September 2026's" volume, unrounded
    over = LAST_DAY >= P_TO

    def every(ok):
        return "failed" if not all(ok) else ("met" if over else "pending")

    R["predictions"] = {"windows_checked": len(ends), "months_checked": len(done),
                        "P1": every(p1), "P3": every(p3), "P2": "met" if record else ("failed" if over else "pending")}
    n_broken = sum(t["status"] == "broken" for t in R["tripwires"])
    # ---- who can move the wallets (read from the contracts; src/fetch_control.py) ----
    with open(os.path.join(RAW, "rpc_wallet_control.json")) as f:
        ctl = json.load(f)

    def approvers(policy):
        role = next(r for r in policy["roles"] if "transfer:VoteApprove" in r["permissions"])
        admin = next(r for r in policy["roles"] if "policy:*" in r["permissions"])  # may change the DAO's own policy: roles, members, thresholds
        return {"members": len(role["kind"]["Group"]), "needed": int(role["vote_policy"]["transfer"]["threshold"]), "names": sorted(role["kind"]["Group"]),
                "policy_needed": int(admin["vote_policy"]["policy"]["threshold"]), "policy_members": len(admin["kind"]["Group"])}

    R["control"] = {"multisig": {"needed": int(ctl["multisig"]["num_confirmations"]), "keys": len(ctl["multisig"]["access_keys"])},
                    "front_end": approvers(ctl["daos"][FRONT]), "oneclick": approvers(ctl["daos"]["1csfundsadmin.sputnik-dao.near"])}
    # ---- HSP-029: the proposal's own text gives the issuance change; the wallet inflow is then set against the target rate ----
    with open(os.path.join(RAW, "gov_hsp029.json")) as f:
        hsp = json.load(f)
    m_rate = re.search(r"maximum annual issuance from ([\d.]+)% to ([\d.]+)% on a smooth (\d+)-month", hsp["text"])
    m_yield = re.search(r"gross staking yield declines from ([\d.]+)% to ([\d.]+)% and ([\d.]+)%", hsp["text"])
    m_status = re.search(r"Status: (\w+)", hsp["text"])
    rate_from, rate_to = float(m_rate.group(1)) / 100, float(m_rate.group(2)) / 100
    issued_day_target = float(supply[s1]) * rate_to / 365
    R["hsp029"] = {"title": hsp["title"], "status": m_status.group(1), "rate_from": rate_from, "rate_to": rate_to, "months": int(m_rate.group(3)),
                   "yield_now": float(m_yield.group(1)) / 100, "yield_year1": float(m_yield.group(2)) / 100, "yield_year2": float(m_yield.group(3)) / 100,
                   "issued_per_day_target": issued_day_target, "coverage_28d_at_target": R["buyback"]["in_28d_per_day"] / issued_day_target,
                   "growth_needed_at_target": issued_day_target / R["buyback"]["in_28d_per_day"],
                   "last_avg3_at_target": None}
    m_unstaked = re.search(r"does not stake, which is currently ([\d.]+)% of supply", hsp["text"])
    R["hsp029"]["unstaked_share"] = float(m_unstaked.group(1)) / 100
    # ---- durability on the investable variable: did the shocks dent what reaches the wallets? ----
    flow_win = {"august": c_win["august"], "before": (T - pd.Timedelta(days=HORIZON), T - day), "event": (T, T + pd.Timedelta(days=HORIZON - 1)),
                "after": c_win["after"]}
    R["buyback"]["around_shocks"] = {k: {"from": str(a.date()), "to": str(b.date()),
                                         "near_per_day": float(held[b] - held[a - day]) / ((b - a).days + 1),
                                         "usd_per_day": float(rev_all[a:b].mean())} for k, (a, b) in flow_win.items()}
    aw = R["buyback"]["around_shocks"]
    R["buyback"]["event_vs_august_near"] = aw["event"]["near_per_day"] / aw["august"]["near_per_day"] - 1
    R["buyback"]["event_vs_august_usd"] = aw["event"]["usd_per_day"] / aw["august"]["usd_per_day"] - 1
    R["buyback"]["event_vs_before_near"] = aw["event"]["near_per_day"] / aw["before"]["near_per_day"] - 1
    # ---- what a holder's outcome depends on, to the end of 2029 (arithmetic on stated assumptions, not a forecast) ----
    yrs = (pd.Timestamp("2029-12-31") - w1).days / 365
    g_now, g_tgt = R["long_term"]["supply_growth_pct_yr"], rate_to
    y_now, y_tgt = R["hsp029"]["yield_now"], R["hsp029"]["yield_year2"]
    R["holder"] = {
        "years": yrs,
        "unstaked_share_change_now": float((1 / (1 + g_now)) ** yrs - 1), "unstaked_share_change_target": float((1 / (1 + g_tgt)) ** yrs - 1),
        "staked_share_change_now": float(((1 + y_now) / (1 + g_now)) ** yrs - 1), "staked_share_change_target": float(((1 + y_tgt) / (1 + g_tgt)) ** yrs - 1),
        # price in 2029 relative to today = revenue growth x change in the revenue multiple / supply growth
        "multiple_now": R["stake"]["mcap_to_revenue"],
        "returns": [{"growth": g, "multiple_share": m, "multiple": m * R["stake"]["mcap_to_revenue"],
                     "price_change": float((1 + g / 100) ** yrs * m / (1 + g_tgt) ** yrs - 1)} for g in (0, 50, 100) for m in (0.25, 0.5, 1.0)],
    }
    # ---- rating rule (RATING.md, written 2026-11-11 after the wallet measurement; deviation 7) ----
    # Buy needs the wallets' inflow to average BUY_NEAR a day over three full calendar months: a quarter of the issuance
    # measured on 2026-11-09, fixed in NEAR in RATING.md so that a cut in issuance (HSP-029) cannot trigger it by itself.
    BUY_NEAR = 21700
    BUY_LEVEL = BUY_NEAR / issued_day
    ml = R["buyback"]["monthly"]
    months_r = [{"m": x["m"], "coverage": x["coverage"],
                 "avg3": None if k < 2 else float(np.mean([y["coverage"] for y in ml[k - 2:k + 1]]))} for k, x in enumerate(ml)]
    for x in months_r:
        x["buy"] = x["avg3"] is not None and x["avg3"] * issued_day >= BUY_NEAR
    # RATING.md counts the order-flow tripwire as broken if it breaks under either set of comparison venues.
    n_broken_rule = n_broken + int(R["tripwires"][0]["status"] == "holding" and R["tripwires"][0]["status_literal"] == "broken")
    flow_ok = n_broken_rule < 2
    wallets_ok = bool(held[w1] >= held[w1 - pd.Timedelta(days=HORIZON)])
    label = "Avoid" if not (flow_ok and wallets_ok) else "Buy" if months_r[-1]["buy"] else "Hold"
    C_FROM, C_TO = pd.Timestamp("2026-12-08"), pd.Timestamp("2027-03-31")
    c_ends = pd.date_range(C_FROM, min(C_TO, w1))
    c1 = all(held[e] >= held[e - pd.Timedelta(days=HORIZON)] for e in c_ends)
    c2 = any(x["buy"] for x in months_r if "2026-12" <= x["m"] <= "2027-03")
    c_over = w1 >= C_TO
    avg3 = [x["avg3"] for x in months_r if x["avg3"] is not None]
    R["hsp029"]["last_avg3_at_target"] = avg3[-1] * issued_day / issued_day_target
    R["rating"] = {"label": label, "flow_ok": flow_ok, "wallets_ok": wallets_ok, "months": months_r, "buy_level": BUY_LEVEL,
                   "last_month": months_r[-1]["m"], "last_avg3": avg3[-1], "best_avg3": max(avg3), "first_avg3": avg3[0],
                   "months_buy": [x["m"] for x in months_r if x["buy"]],
                   "month_min": min(x["coverage"] for x in months_r), "month_max": max(x["coverage"] for x in months_r),
                   "need_per_day": BUY_NEAR, "need_vs_last_avg3": BUY_LEVEL / avg3[-1],
                   "dilution_to_2029": float(1 - 1 / (1 + R["long_term"]["supply_growth_pct_yr"]) ** ((pd.Timestamp("2029-12-31") - w1).days / 365)),
                   "scenarios": {str(g): float(R["buyback"]["coverage_28d"] * (1 + g / 100) ** ((pd.Timestamp("2029-12-31") - w1).days / 365)) for g in (0, 25, 50, 100)},
                   "calls": {"windows_checked": len(c_ends), "C1": "failed" if not c1 else ("met" if c_over else "pending"),
                             "C2": "met" if c2 else ("failed" if c_over else "pending")}}
    # The position shown is the rating. archive/PREDICTIONS-2026-11-10.md's timestamped position was Long; see deviation 7.
    R["position"] = {"n_broken": n_broken_rule, "n": len(R["tripwires"]), "label": label,
                     "timestamped": "Long" if n_broken == 0 else "Long, one tripwire broken" if n_broken == 1 else "Neutral"}

    os.makedirs(os.path.join(ROOT, "data", "processed"), exist_ok=True)
    with open(os.path.join(ROOT, "data", "processed", "results.json"), "w") as f:
        json.dump(R, f, indent=1)
    write(os.path.join(ROOT, "docs", "data.js"), "window.RESULTS = " + json.dumps(R, separators=(",", ":")) + ";\n")
    render(R)
    return R


def render(R):
    """Fill THESIS.template.md and README.template.md. {{a.b|fmt}} looks up R['a']['b']; a missing key is an error."""
    tpath = os.path.join(ROOT, "THESIS.template.md")
    fmts = {"pct": lambda v: f"{100 * v:+.1f}%", "pct0": lambda v: f"{100 * v:+.0f}%", "upct": lambda v: f"{100 * abs(v):.1f}%",
            "share": lambda v: f"{100 * v:.1f}%", "spct0": lambda v: f"{100 * v:+,.0f}%", "pp": lambda v: f"{100 * v:.1f} points", "p": lambda v: "< 0.01" if v == 0 else "> 0.99" if v == 1 else f"{v:.2f}", "peq": lambda v: "p < 0.01" if v == 0 else "p > 0.99" if v == 1 else f"p = {v:.2f}", "usd_m": lambda v: f"${v / 1e6:,.1f}M",
            "usd_b": lambda v: f"${v / 1e9:,.2f}B", "usd_k": lambda v: f"${v / 1e3:,.0f}k", "bps": lambda v: f"{v:.1f}",
            "n": lambda v: f"{v:,.0f}", "f2": lambda v: f"{v:.2f}", "x": lambda v: f"{v:.1f}×", "f1": lambda v: f"{v:.1f}", "f0x": lambda v: f"{v:.0f} times", "pct2": lambda v: f"{100 * v:.2f}%", "usd_k1": lambda v: f"${v / 1e3:,.0f}k", "f2pct": lambda v: f"{100 * v:.2f}%", "upct0": lambda v: f"{100 * v:,.0f}%", "months": lambda v: ", ".join(pd.Timestamp(x + "-01").strftime("%b %Y") for x in v), "share0": lambda v: f"{100 * v:.0f}%", "share_inv": lambda v: f"{100 * (1 - v):.0f}%", "month": lambda v: pd.Timestamp(v + "-01").strftime("%b %Y"), "m_near": lambda v: f"{v / 1e6:,.1f}M", "list": lambda v: ", ".join(v), "s": str}

    def sub(m):
        path, _, fmt = m.group(1).partition("|")
        v = R
        for part in path.split("."):
            v = v[part] if isinstance(v, dict) else v[int(part)]
        return fmts[fmt or "s"](v)

    def fill(name):
        with open(os.path.join(ROOT, name + ".template.md")) as f:
            return re.sub(r"\{\{([^}]+)\}\}", sub, f.read())

    text = fill("THESIS")
    write(os.path.join(ROOT, "THESIS.md"), text)
    write(os.path.join(ROOT, "README.md"), fill("README"))
    appendix = fill("APPENDIX")
    write(os.path.join(ROOT, "APPENDIX.md"), appendix)
    write(os.path.join(ROOT, "docs", "appendix.html"), THESIS_PAGE.replace("{{body}}", markdown.markdown(appendix, extensions=["tables", "fenced_code"]).replace('href="THESIS.md"', 'href="thesis.html"')).replace("<title>NEAR Intents Thesis</title>", "<title>NEAR Intents Thesis: Appendix</title>"))
    body = markdown.markdown(text, extensions=["tables", "fenced_code"])
    write(os.path.join(ROOT, "docs", "thesis.html"), THESIS_PAGE.replace("{{body}}", body.replace('href="APPENDIX.md"', 'href="appendix.html"')))
    # The rating page: a plain summary generated from results.json, then RATING.md as timestamped, word for word, folded
    # away. The first version (archive/PREDICTIONS-2026-11-10.md, which said Long) is named and linked, not reprinted:
    # it is superseded, and reprinting it in full read as if it were still the call.
    st = lambda v: v.capitalize()
    summary = re.sub(r"\{\{([^}]+)\}\}", sub, f"""# The rating and five dated calls

**Rating: {{{{position.label}}}}**, to the end of 2029. Keep the NEAR you own, staked; do not add yet. First review: 31 March 2027.

The rating follows a written rule, computed on every build (`src/build.py`).

| Rating | When | Now |
|---|---|---|
| **Buy** | The wallets that receive Intents' revenue gain {{{{rating.need_per_day|n}}}} NEAR a day or more ({{{{rating.buy_level|share0}}}} of new supply), averaged over three full months | {{{{buyback.last3_per_day|n}}}} a day ({{{{rating.last_avg3|share0}}}}) |
| **Hold** | Otherwise | **{{{{position.label}}}}** |
| **Avoid** | The three wallets hold less NEAR than 28 days earlier, or two of the three warning measures break (Intents' volume against rival venues, the fee it earns per dollar, Zcash held on Intents) | Wallets growing; {{{{position.n_broken}}}} of {{{{position.n}}}} broken |

Five calls, scored only on data after 11 November 2026 and resolved on 31 March 2027. Three are about the business, two about the wallets.

| | The call | If it fails | Status |
|---|---|---|---|
| P1 | Intents' volume stays above its limit against rival venues in every 28-day window | Trust shocks or rivals are taking share | {st(R["predictions"]["P1"])} |
| P2 | Intents sets a new monthly volume record, above {{{{long_term.record_month|month}}}}'s {{{{long_term.record_volume|usd_b}}}}, between December and March | Growth has stalled | {st(R["predictions"]["P2"])} |
| P3 | The fee Intents earns per dollar stays above {{{{windows.estimation.take_rate_bps|bps}}}} bps in every 28-day window | It is buying volume with price | {st(R["predictions"]["P3"])} |
| C1 | The three wallets keep their NEAR in every 28-day window | It is a treasury being spent, not a buyback | {st(R["rating"]["calls"]["C1"])} |
| C2 | The wallets reach {{{{rating.need_per_day|n}}}} NEAR a day over three months. A test, not a forecast: if it is met, the rule says Buy | What reaches NEAR is not growing fast enough, and Hold stands | {st(R["rating"]["calls"]["C2"])} |

Scoring after 31 March 2027: `make fetch && END_DATE=2027-03-31 make fetch-bq && LAST_DAY=2027-03-31 make`.
""")
    with open(os.path.join(ROOT, "RATING.md")) as f:
        rating_md = f.read()
    preds = (markdown.markdown(summary, extensions=["tables"])
             + "<h2>The rule as timestamped</h2><p><code>RATING.md</code> is timestamped with OpenTimestamps, so it is shown word for word: "
               "editing it would break its proof. It holds the exact thresholds and the reasoning behind the Buy level.</p>"
             + "<details><summary>Show RATING.md</summary>" + markdown.markdown(rating_md, extensions=["tables"]) + "</details>"
             + "<p><em>An earlier version of the calls, timestamped on 10 November 2026 (Bitcoin block 975308), rated NEAR Long before the "
               "revenue wallets were measured. It is superseded by the rule above and kept unchanged in "
               "<code>archive/PREDICTIONS-2026-11-10.md</code> so its proof still verifies; the change is explained in the thesis.</em></p>")
    write(os.path.join(ROOT, "docs", "predictions.html"), THESIS_PAGE.replace("{{body}}", preds).replace("<title>NEAR Intents Thesis</title>", "<title>NEAR Intents: Rating and Calls</title>"))


THESIS_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NEAR Intents Thesis</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Mona+Sans:wght@400..800&family=Hanken+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css">
</head>
<body>
<div class="band"><div class="in"><span>Digital Assets Research · Investment Thesis</span><span>NEAR Hackathon 2026 · Investment Thesis Track</span></div></div>
<main class="prose">
<p class="back"><a href="index.html">← Dashboard</a></p>
{{body}}
</main>
</body>
</html>
"""


if __name__ == "__main__":
    R = main()
    h1 = R["H1"]
    lit = h1["literal"]
    print(f"H1 abnormal volume, {HORIZON} days from {R['events']['T']}: {100 * lit['stat_pct']:+.1f}% (pre-registered donors, p = {lit['p_placebo_time']:.2f}), "
          f"{100 * h1['stat_pct']:+.1f}% (narrower set, p = {h1['p_placebo_time']:.2f})  ->  {h1['verdict']}")
