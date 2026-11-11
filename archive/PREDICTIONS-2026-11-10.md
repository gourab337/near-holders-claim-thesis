# Predictions: what this thesis says will happen next

Written 2026-11-11, after the analysis and before any of the data that will score them exists. The SHA-256 of this file is timestamped with OpenTimestamps (`PREDICTIONS.md.ots`). Each prediction is scored from the same pipeline: `make fetch && make fetch-bq && make`.

The thesis is: NEAR Intents' order flow survives trust shocks, so the long-term case for NEAR rests on Intents growing again. These three predictions are what that thesis commits to. If any one fails, the thesis is wrong in the way the prediction names.

| | Prediction | Resolves | Scored from | If it fails |
|---|---|---|---|---|
| P1 | **Flow stays durable.** In every 28-day window ending from 2026-12-08 to 2027-03-31 (so every day scored is after 2026-11-10), Intents volume stays above the calm-period limit against the pre-registered model (abnormal volume above −29.5%). | 2027-03-31 | the order-flow tripwire in `src/build.py` | Trust shocks or rivals are taking share: the durability half of the thesis fails. |
| P2 | **Growth comes back.** Intents sets a new monthly volume record, above September 2026's $4.80B, in at least one calendar month from December 2026 to March 2027 (November is excluded because its first days are already observed). | 2027-03-31 | DefiLlama monthly volume, as in Exhibit 2 | Growth has stalled for 18 months: the growth half of the thesis fails. |
| P3 | **Price holds.** In every 28-day window ending from 2026-12-08 to 2027-03-31 (so every day scored is after 2026-11-10), the take rate stays above the calm-period average of 13.6 bps. | 2027-03-31 | the take-rate tripwire in `src/build.py` | Intents is buying volume with price, and revenue per dollar falls. |

## Position

**Long NEAR.** One of the three tripwires (Zcash balances) is broken now. The position moves to neutral if a second tripwire breaks, or if P2 fails on 2027-03-31.
