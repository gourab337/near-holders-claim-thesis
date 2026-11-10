"""Rebuild every number and chart input from data/raw/. No network.

Follows PREREGISTRATION.md. Outputs:
  data/processed/results.json   every number quoted anywhere
  docs/data.js                  the same, for the static dashboard
  THESIS.md                     rendered from THESIS.template.md
  README.md                     rendered from README.template.md
  docs/thesis.html              the same thesis as a web page
  docs/predictions.html         PREDICTIONS.md as a web page
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
LAST_DAY = pd.Timestamp("2026-11-09")  # last complete UTC day in the snapshot
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

    est = (panel.index >= EST_START) & (panel.index <= EST_END)
    evt = (panel.index >= T) & (panel.index < T + pd.Timedelta(days=HORIZON))
    assert est.sum() == EST_LEN and evt.sum() == HORIZON

    # Donor rule: usable only with a positive value on every day the design touches.
    first_needed = panel.index.min()
    dropped = {}
    for d in DONORS_PREREG:
        s = panel[d]
        if s[est].isna().any() or (s[est] <= 0).any():
            dropped[d] = "missing or zero days in the estimation window (pre-registered rule)"
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
                 "share_negative": float((g < 0).mean()), "share_below_mde": float((g < R["H1"]["mde_pct"]).mean())}

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
               "active_per_day_median": float(active.median()), "n_placebo": int(len(h5_placebo)),
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

    # ---- long-term view (added after the pre-registration) ------------------------------
    vol_all, rev_all = llama_series("intents_volume"), llama_series("intents_revenue")
    month_end = LAST_DAY.to_period("M").start_time  # first day of the current, incomplete month
    monthly = pd.DataFrame({"volume": vol_all.resample("MS").sum(), "revenue": rev_all.resample("MS").sum()})
    monthly = monthly[monthly.index < month_end]
    chain_supply = pd.read_csv(os.path.join(RAW, "bq_circulating_supply.csv"), parse_dates=["block_date"]).set_index("block_date") / 1e24
    supply = chain_supply.total_tokens_supply  # NEAR's own supply table (BigQuery): issuance net of burns
    s1 = LAST_DAY
    s0 = s1 - pd.Timedelta(days=365)
    supply_growth_yr = float(supply[s1] - supply[s0])
    buyback_yr = R["stake"]["revenue_annualised"] / float(near.price[LAST_DAY])  # upper bound: all revenue buys NEAR
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
        "buyback_near_yr": buyback_yr, "buyback_coverage": buyback_yr / supply_growth_yr,
        "growth_needed": supply_growth_yr / buyback_yr,
    }
    first_peak = monthly.volume[:monthly.volume.idxmax() - pd.DateOffset(months=9)].idxmax()  # the first surge's peak
    capture_now = R["stake"]["revenue_30d"] / R["stake"]["volume_30d"] * 1e4
    R["long_term"].update({
        "first_peak_month": str(first_peak.date())[:7], "first_peak_volume": float(monthly.volume[first_peak]),
        "last_vs_first_peak": float(monthly.volume[last_m] / monthly.volume[first_peak]),
        "capture_now_bps": capture_now,
        "growth_needed_calm_capture": R["long_term"]["growth_needed"] * capture_now / R["windows"]["estimation"]["capture_bps"],
        "growth_needed_calm_price": R["long_term"]["growth_needed"] * R["windows"]["estimation"]["near_price"] / float(near.price[LAST_DAY]),
    })

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
    n_broken = sum(t["status"] == "broken" for t in R["tripwires"])
    # Position rule, set after seeing results (deviation 6): long while all hold, under review at one break, neutral at two.
    R["position"] = {"n_broken": n_broken, "n": len(R["tripwires"]),
                     "label": "Long" if n_broken == 0 else "Long, one tripwire broken" if n_broken == 1 else "Neutral"}

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
            "share": lambda v: f"{100 * v:.1f}%", "p": lambda v: f"{v:.2f}", "usd_m": lambda v: f"${v / 1e6:,.1f}M",
            "usd_b": lambda v: f"${v / 1e9:,.2f}B", "usd_k": lambda v: f"${v / 1e3:,.0f}k", "bps": lambda v: f"{v:.1f}",
            "n": lambda v: f"{v:,.0f}", "f2": lambda v: f"{v:.2f}", "x": lambda v: f"{v:.1f}×", "share0": lambda v: f"{100 * v:.0f}%", "month": lambda v: pd.Timestamp(v + "-01").strftime("%b %Y"), "m_near": lambda v: f"{v / 1e6:,.1f}M", "list": lambda v: ", ".join(v), "s": str}

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
    body = markdown.markdown(text, extensions=["tables", "fenced_code"])
    write(os.path.join(ROOT, "docs", "thesis.html"), THESIS_PAGE.replace("{{body}}", body))
    with open(os.path.join(ROOT, "PREDICTIONS.md")) as f:  # frozen and timestamped, so rendered as is
        preds = markdown.markdown(f.read(), extensions=["tables"])
    write(os.path.join(ROOT, "docs", "predictions.html"), THESIS_PAGE.replace("{{body}}", preds).replace("<title>NEAR Intents Thesis</title>", "<title>NEAR Intents Predictions</title>"))


THESIS_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NEAR Intents Thesis</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
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
    print(f"H1 abnormal volume, {HORIZON} days from {R['events']['T']}: {100 * h1['stat_pct']:+.1f}%  "
          f"placebo-in-time p = {h1['p_placebo_time']:.2f}  ->  {h1['verdict']}")
