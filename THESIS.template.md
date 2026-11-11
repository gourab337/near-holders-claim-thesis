# Hold NEAR. Intents is a resilient business, but NEAR holders get little of what it earns so far.

*It came through a freeze and a hack with its volume intact. But the NEAR it sends back offsets only {{buyback.coverage_28d|share0}} of the new NEAR issued, none of it is paid to holders, and no rule in code protects it.*

NEAR HACKATHON 2026 · Investment Thesis track · data to {{last_day}} · about ten minutes to read · full tables, method and caveats: [`APPENDIX.md`](APPENDIX.md)

## The claim

The case for owning NEAR rests on one business. NEAR Intents swaps tokens across blockchains, and part of what it earns is sent back as NEAR. NEAR's market value is {{stake.mcap_to_revenue|n}} times a year of that revenue. A price like that needs two things to be true: the business keeps going, and holders share in it.

The first is true. The second, so far, is not. Here is the argument in four steps.

1. **The business is resilient.** Within a month Intents froze users' funds and was then hacked for $3.8M. Its volume barely moved: {{confidential.oneclick_event_vs_august|pct0}} against August.
2. **One number looked like a loss. It was not.** On NEAR's public chain, swaps fell from {{privacy.events.windows.before.token_diff|n}} a day to {{privacy.events.windows.after.token_diff|n}}. They had not left. On 27 October Intents began settling swaps off the public chain. The business was fine, but it became harder to check.
3. **Holders get little of it.** NEAR creates {{buyback.issued_per_day|n}} new tokens a day, which dilutes holders. The wallets that receive Intents' revenue take in {{buyback.in_28d_per_day|n}} a day: {{buyback.coverage_28d|share0}} as much. To match all the new supply, the inflow would have to grow about {{buyback.growth_needed|x}}.
4. **And no rule protects even that.** None of it is paid to holders, staked or burned. A few signers can move it.

**So the rating is {{position.label}}.** A resilient business is a reason not to sell. A small share that nobody guarantees is a reason not to buy more. Keep the NEAR you own, staked, and do not add; the horizon is the end of 2029. The rating turns to Buy when the wallets take in {{rating.need_per_day|n}} NEAR a day ({{rating.buy_level|share0}} of new supply) for three full months. The last three full months averaged {{buyback.last3_per_day|n}} ({{rating.last_avg3|share0}}). It turns to Avoid if the wallets shrink or two of its three warning measures break. The rule is timestamped in [`RATING.md`](RATING.md), with five dated predictions that resolve on 31 March 2027.

## Evidence for the rating

### Part 1. The business is resilient

**In one line: Intents took two hits to its users' trust in one month, and the money kept flowing.**

The two hits:

- **{{events.T}}: a freeze.** Intents' compliance system blocked more than $50M of transfers linked to the Bitget hack and froze $503k in the middle of a swap. Three weeks earlier a Zcash user had reported $589k held for 50 days.
- **{{events.E2}}: a hack.** $3.8M was taken, and the contract was paused on eleven networks. The funds were returned the next day.

Critics had a simple prediction: a venue that can freeze your money is not trustless, so users will leave the first time it does. This was the test of that prediction.

I counted every swap of $10,000 or more on 1Click, the swap service that apps plug into. These large swaps are about three-quarters of 1Click's dollars.

Volume and the number of apps were about the same before, during and after.

| | August | 4 weeks from the freeze | Since late October |
|---|---|---|---|
| Large-swap volume a day | {{large.windows.august.usd_per_day|usd_m}} | {{large.windows.event.usd_per_day|usd_m}} | {{large.windows.after.usd_per_day|usd_m}} |
| Apps routing large swaps | {{large.windows.august.integrators}} | {{large.windows.event.integrators}} | {{large.windows.after.integrators}} |

- **The volume stayed.** In the four weeks from the freeze, large-swap volume was {{large.usd_event_vs_august|pct0}} against August, and all 1Click volume {{confidential.oneclick_event_vs_august|pct0}}.
- **The apps stayed.** Most of this volume arrives through apps that build Intents into their own products. Of the {{large.august_big}} apps that routed $1M or more in August, {{large.windows.event.august_big_kept_half}} kept at least half their volume.
- **Revenue did not fall.** Intents earned {{buyback.around_shocks.august.usd_per_day|usd_k}} a day in August and {{buyback.around_shocks.event.usd_per_day|usd_k}} a day in the four weeks after the freeze. Why it rose that much is outside this thesis; the appendix has the detail.

Two cautions:

- **One app carries a third of it.** Since 27 October {{large.top1}} has routed {{large.windows.after.top1_share|share0}} of large-swap dollars. A decision at one company could move more volume than the freeze did.
- **Individual users came back less.** Of addresses that sent large swaps on five or more days before the freeze, {{large.senders.5.rate|share0}} came back ({{large.senders.5.n}} addresses). In the one calm period I can compare with, {{large.senders.5.calm_min|share0}} to {{large.senders.5.calm_max|share0}} did.

So some individual users did pull back. But the customer that decides is the app, not the end user, and most apps did not leave.

### Part 2. The drop that was not a drop

**In one line: public swaps on the chain fell by about four-fifths, but the swaps had moved out of view, not away.**

If the business held, the public chain should show it. It showed the opposite.

| On NEAR's public chain, a day | August | From late October |
|---|---|---|
| Swaps recorded | {{privacy.events.windows.before.token_diff|n}} | {{privacy.events.windows.after.token_diff|n}} |

On its face that is users leaving after the freeze, exactly as the critics predicted.

It is not. On 27 October 2026 NEAR Intents' changelog said: "From October 27, 2026, 1Click swaps settle confidentially." The swap now happens on what the changelog calls "a permissioned instance of the NEAR protocol operated by a small validator set with no public networking". The public chain shows only money going into a Treasury account and coming out again.

I tested this directly. I drew 300 successful swaps at random on each of five days and followed each one onto the chain (`src/fetch_explorer.py`, `sql/intents_swap_trace.sql`).

| Of the sampled swaps | 12 Aug | 15 Sep | 26 Oct | 28 Oct | 5 Nov |
|---|---|---|---|---|---|
| Left a public record of the swap | **{{confidential.trace.2026-08-12.public|share0}}** | {{confidential.trace.2026-09-15.public|share0}} | {{confidential.trace.2026-10-26.public|share0}} | {{confidential.trace.2026-10-28.public|share0}} | **{{confidential.trace.2026-11-05.public|share0}}** |
| Went through the Treasury account | **{{confidential.trace.2026-08-12.treasury|share0}}** | {{confidential.trace.2026-09-15.treasury|share0}} | {{confidential.trace.2026-10-26.treasury|share0}} | {{confidential.trace.2026-10-28.treasury|share0}} | **{{confidential.trace.2026-11-05.treasury|share0}}** |

In my samples the change was rolled out over about a week: {{confidential.trace.2026-10-28.treasury|share0}} went through the Treasury account on 28 October and {{confidential.trace.2026-11-05.treasury|share0}} by 5 November.

The swaps did not stop. Counted through Intents' own records, 1Click volume was {{confidential.windows.august.oneclick_usd|usd_m}} a day in August and {{confidential.windows.after.oneclick_usd|usd_m}} a day after the switch. What disappeared is the public record of them. The sampled swaps were funded by normal public deposits, so this was a change in how 1Click settles, not users choosing privacy. Why NEAR Intents made the change, I cannot say.

**What it costs a holder.** The business did not shrink, but it became harder to check. The Intents volume that DefiLlama shows is read from a dataset NEAR itself publishes. Counted in dollars, public swaps were {{privacy.windows.after_ga|share0}} of that figure in the summer and {{privacy.windows.after|share0}} from late October. I have no evidence that the reported number is wrong. But a holder can no longer verify most of it without relying on the operator.

### Part 3. But little of it reaches NEAR holders

**In one line: Intents sends back {{buyback.coverage_28d|share0}} as much NEAR as NEAR issues, and the amount is not growing steadily.**

A resilient business only helps a token holder if the holder gets a share. Here is the share.

NEAR issues new tokens every day, and that dilutes everyone who holds it. The fair test of Intents' value to a holder is how much of that dilution its revenue offsets.

Since February 2026, part of Intents' revenue has been swept, as NEAR, into three wallets: a buybacks wallet, a fund fed by 1Click fees and a fund fed by front-end fees. DefiLlama calls this a buyback and credits it to NEAR's holders. The wallets are public, so I read their balances for every day of the past year from NEAR's BigQuery dataset (`sql/revenue_wallets_daily.sql`).

| | |
|---|---|
| NEAR the wallets gain a day (last 28 days) | {{buyback.in_28d_per_day|n}} |
| NEAR issued a day | {{buyback.issued_per_day|n}} |
| The wallets' gain as a share of new supply | **{{buyback.coverage_28d|share0}}** |
| Growth needed to match all of it | **about {{buyback.growth_needed|x}}** |

My count comes to {{buyback.wallets_vs_defillama|share}} of the revenue DefiLlama reports for the same days, so the two sources agree on the size.

**It is not growing steadily.** By month, the share of new supply that came back has run from {{rating.month_min|share0}} ({{buyback.low_month|month}}) to {{rating.month_max|share0}} ({{buyback.best_month|month}}), with no steady rise. Revenue in dollars grew {{buyback.usd_last_vs_first_month|x}} between {{buyback.first_month|month}} and {{buyback.last_month|month}}, but NEAR's price rose {{buyback.price_last_vs_first_month|x}}, so the extra dollars bought no extra NEAR. That is the catch in any buyback: when the token goes up, the same dollars buy less of it.

### Part 4. And no rule protects even that

**In one line: none of this NEAR is paid to holders, staked or burned, and a few signers can move it.**

A small share would still be worth something if holders were sure to get it. They are not. Nothing in code sends this NEAR to holders. It sits in the three wallets, and I read from the contracts who can move it (`src/fetch_control.py`).

| Wallet | Who can move the NEAR |
|---|---|
| Buybacks wallet | {{control.multisig.needed}} of {{control.multisig.keys}} keys |
| 1Click fund | {{control.oneclick.needed}} of {{control.oneclick.members}} members |
| Front-end fund | {{control.front_end.needed}} of {{control.front_end.members}} members. But its policy sets the threshold for changing the fund's own rules at {{control.front_end.policy_needed}} vote (read from the contract, not tested). |

So far the signers have left it alone: the balance fell on {{buyback.outflow_days}} of {{buyback.days}} days. But that is their choice, not a rule.

### So: Hold

**In one line: a resilient business is a reason not to sell; a small share that nobody guarantees is a reason not to buy more.**

The price is what makes the small share matter. NEAR's market value is {{stake.mcap_to_revenue|n}} times a year of Intents' revenue, so the price already assumes years of growth. The table shows the change in NEAR's price by the end of 2029, given how fast Intents revenue grows and what multiple of revenue the market still pays. It is arithmetic, not a forecast. Supply keeps growing in every cell, which is why the price slips even where nothing else changes.

| Intents revenue growth a year | Multiple falls to a quarter ({{holder.returns.0.multiple|n}}×) | Multiple halves ({{holder.returns.1.multiple|n}}×) | Multiple holds ({{holder.returns.2.multiple|n}}×) |
|---|---|---|---|
| 0% | {{holder.returns.0.price_change|spct0}} | {{holder.returns.1.price_change|spct0}} | {{holder.returns.2.price_change|spct0}} |
| 50% | {{holder.returns.3.price_change|spct0}} | {{holder.returns.4.price_change|spct0}} | {{holder.returns.5.price_change|spct0}} |
| 100% | {{holder.returns.6.price_change|spct0}} | {{holder.returns.7.price_change|spct0}} | {{holder.returns.8.price_change|spct0}} |

A holder loses wherever growth stops, and gains only if revenue compounds and the market keeps paying a high multiple for it. That is why a resilient business is not enough for a Buy. And because the business did come through a freeze and a hack, there is no case to sell either. So: Hold.

**Why "keep it staked".** New NEAR goes to stakers. By the end of 2029, a holder who does not stake owns {{holder.unstaked_share_change_now|upct}} less of the supply at today's issuance. A holder who stakes owns {{holder.staked_share_change_now|upct}} more, before the validator's fee.

## Evidence against

- **I changed the rating a day before submitting.** I timestamped Long, which is this rule's Buy, on 10 November. On 11 November I measured the wallets and moved to Hold. I set the Buy level after seeing the data, so the fact that it fits the past proves nothing. Only the five dated predictions below test it.
- **Hold is close to Avoid.** The rule watches three warning measures, called tripwires and listed below. One is already broken: Zcash held on Intents, the balances of the users most exposed to a freeze, fell past its limit. Another holds by about a point: Intents' volume over the latest 28 days against what rival venues' volumes predict ({{tripwires.0.value_literal|pct}} against a limit of {{tripwires.0.limit_literal|pct}}). That compares Intents with rivals, not with its own past, so it is a different measure from the {{confidential.oneclick_event_vs_august|pct0}} in Part 1.
- **The test I planned in advance was inconclusive.** It compares Intents' reported volume, over the 28 days from the freeze, with a model built from rival venues. It could only detect a loss larger than {{H1.literal.mde_pct|upct}}. It found {{H1.literal.stat_pct|pct}} or {{H1.stat_pct|pct}}, depending on which rival venues I compare with, and neither can be told from noise. Part 1 rests on the direct counts, not on this test.
- **Part of the good news comes from the operator's own data.** The swap counts in Parts 1 and 2 come from NEAR Intents' Explorer API. It is a second source, but not an independent one.
- **The bull has a real point that my rule ignores.** NEAR's governance has passed a cut in maximum issuance from {{hsp029.rate_from|share}} to {{hsp029.rate_to|share}} over {{hsp029.months}} months (HSP-029). At that rate the same inflow would cover {{hsp029.coverage_28d_at_target|share0}} of new supply instead of {{buyback.coverage_28d|share0}}. The Buy level is fixed in NEAR a day so that this cannot trigger a Buy by itself: it says nothing about whether Intents sends more to NEAR.
- **It is four weeks, and one business.** Four weeks after a shock is not the long term. And if value reaches NEAR holders some other way than Intents, this thesis does not see it.

The full list, with every number, is in the appendix (B6).

## What would change my mind

The rating follows a rule, computed on every build (`src/build.py`).

| Rating | When | Now |
|---|---|---|
| **Buy** | The wallets gain {{rating.need_per_day|n}} NEAR a day or more ({{rating.buy_level|share0}} of new supply), averaged over three full months | {{buyback.last3_per_day|n}} a day ({{rating.last_avg3|share0}}) |
| **Hold** | Otherwise | **{{position.label}}** |
| **Avoid** | The three wallets hold less NEAR than 28 days earlier, or two of three tripwires break (order flow against rivals, the fee Intents earns per dollar, Zcash held on Intents) | Wallets growing; {{position.n_broken}} of {{position.n}} tripwires broken |

Five dated calls, scored only on data after 11 November 2026 and resolved on 31 March 2027. Three are about the business (P1 to P3) and two about the wallets (C1 and C2).

| | The call | If it fails |
|---|---|---|
| P1 | The flow stays above its limit against rival venues | Trust shocks or rivals are taking share |
| P2 | Intents sets a new monthly volume record, above September's | Growth has stalled |
| P3 | The fee Intents earns per dollar holds | It is buying volume with price |
| C1 | The wallets keep their NEAR | It is a treasury being spent, not a buyback |
| C2 | The wallets reach {{rating.need_per_day|n}} NEAR a day over three months. This is a test, not a forecast: if it is met, the rule says Buy | What reaches NEAR is not growing fast enough to matter, and Hold stands |

Three things are outside the rule, and I would review the rating if any happened:

- **The signers commit the NEAR by a rule in code**: burned, staked, or paid to holders. That would give holders a share that is guaranteed, and it is the one change that needs no growth at all.
- **{{large.top1}}'s share falls by half** with no other app replacing it.
- **NEAR Intents stops publishing 1Click swaps** through its Explorer. Reported volume would then be uncheckable.

## Check it yourself

```bash
make         # rebuilds every number, this file and the dashboard data from data/raw/ (offline, no keys)
make test    # checks on the data, the method and the outputs
make check   # confirms the rebuild reproduces the committed thesis
```

**What was fixed in advance, and what was not.** The study of the freeze and the exploit, with its tests and decision rules, was written down in advance. That file is timestamped in a Bitcoin block mined 29 minutes after the data download began, so the timestamp shows the plan was frozen early, not that it came before the data. Parts 1 to 3 were added after seeing results. The appendix lists every deviation (B7) and the event study in full (Part A).

**Sources.** NEAR's public BigQuery dataset (wallet balances, supply, every transaction to `intents.near`). The NEAR Intents Explorer API (1Click swaps). DefiLlama (reported volume and revenue, rival venues). CoinGecko (prices). NEAR Intents' changelog and NEAR's governance forum. The contracts themselves, over a public RPC endpoint. Links, fetch times and file hashes are in `data/raw/MANIFEST.json`; the incident timeline and its sources are in the appendix.
