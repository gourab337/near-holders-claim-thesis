# Hold NEAR. Intents is a resilient business, but NEAR holders get little of what it earns so far.

*It came through a freeze and a hack with its volume intact. But the NEAR it sends back offsets only 16% of the new NEAR issued, none of it is paid to holders, and no rule in code protects it.*

NEAR HACKATHON 2026 · Investment Thesis track · data to 2026-11-09 · about ten minutes to read · full tables, method and caveats: [`APPENDIX.md`](APPENDIX.md)

## The claim

Most of the revenue that can be measured on NEAR comes from one business. NEAR Intents swaps tokens across blockchains, and part of what it earns is sent back as NEAR. Over the last 30 days it earned 86% of the revenue DefiLlama tracks on NEAR, about 17 times what the NEAR chain itself earns in fees. NEAR's other lines of business, such as NEAR AI Cloud, are not in that count. NEAR's market value is 213 times a year of Intents' revenue.

So for a NEAR holder, two things about Intents matter most: the business keeps going, and holders share in it.

The first is true. The second, so far, is not. Here is the argument in four steps.

1. **The business is resilient.** Within a month Intents froze users' funds and was then hacked for $3.8M. Its volume barely moved: -5% against August.
2. **One number looked like a loss. It was not.** From late October, swap volume visible on NEAR's public chain fell from $40.5M a day to $15.0M. Usage did not fall: on 27 October Intents began settling swaps off the public chain, and the big apps kept routing through it. The business was fine, but it became harder to check.
3. **Holders get little of it.** Intents does buy back NEAR with its revenue. But NEAR creates 86,966 new tokens a day, which dilutes holders, and the buyback takes in 13,571: 16% as much. To match all the new supply, it would have to grow about 6.4×. At about $60k a day against $707.0M of NEAR traded, it is also far too small to move the price on its own.
4. **And no rule protects even that.** None of it is paid to holders, staked or burned. A few signers can move it.

**So the rating is Hold.** A resilient business is a reason not to sell. A small share that nobody guarantees is a reason not to buy more. Keep the NEAR you own, staked, and do not add; the horizon is the end of 2029. The rating turns to Buy when the wallets take in 21,700 NEAR a day (25% of new supply) for three full months. The last three full months averaged 15,486 (18%). It turns to Avoid if the wallets shrink or two of its three warning measures break. The rule is timestamped in [`RATING.md`](RATING.md), with five dated predictions that resolve on 31 March 2027.

## Evidence for the rating

### Part 1. The business is resilient

**In one line: Intents took two hits to its users' trust in one month, and the money kept flowing.**

The two hits:

- **2026-09-29: a freeze.** Intents' compliance system blocked more than $50M of transfers linked to the Bitget hack and froze $503k in the middle of a swap. Three weeks earlier a Zcash user had reported $589k held for 50 days.
- **2026-10-01: a hack.** $3.8M was taken, and the contract was paused on eleven networks. The funds were returned the next day.

Critics had a simple prediction: a venue that can freeze your money is not trustless, so users will leave the first time it does. This was the test of that prediction.

I counted every swap of $10,000 or more on 1Click, the swap service that apps plug into. These large swaps are about three-quarters of 1Click's dollars.

Volume and the number of apps were about the same before, during and after.

| | August | 4 weeks from the freeze | Since late October |
|---|---|---|---|
| Large-swap volume a day | $28.9M | $28.5M | $27.6M |
| Apps routing large swaps | 66 | 81 | 64 |

- **The volume stayed.** In the four weeks from the freeze, large-swap volume was -1% against August, and all 1Click volume -5%.
- **The apps stayed.** Most of this volume arrives through apps that build Intents into their own products. Of the 25 apps that routed $1M or more in August, 17 kept at least half their volume.
- **Revenue did not fall.** Intents earned $23k a day in August and $72k a day in the four weeks after the freeze. Why it rose that much is outside this thesis; the appendix has the detail.

Two cautions:

- **One app carries a third of it.** Since 27 October swapkit has routed 37% of large-swap dollars. A decision at one company could move more volume than the freeze did.
- **Individual users came back less.** Of addresses that sent large swaps on five or more days before the freeze, 59% came back (94 addresses). In the one calm period I can compare with, 68% to 75% did.

So some individual users did pull back. But the customer that decides is the app, not the end user, and most apps did not leave.

### Part 2. The drop that was not a drop

**In one line: public swap volume fell by almost two-thirds, but usage did not drop. The swaps had moved out of view, not away.**

If the business held, the public chain should show it. From late October, it showed the opposite.

| Swap volume a day | August | 8 Sep to 26 Oct | From 28 Oct |
|---|---|---|---|
| Visible on NEAR's public chain | $40.5M | $47.8M | **$15.0M** |
| 1Click, counted through Intents' own records | $38.7M | $43.0M | **$36.9M** |

Until 27 October the two moved together. (The public figure also counts swaps outside 1Click, so it starts a little higher.) After it, the public figure fell by almost two-thirds while 1Click held. Read only from the chain, that looks like users leaving after the freeze, exactly as the critics predicted.

It is not. On 27 October 2026 NEAR Intents' changelog said: "From October 27, 2026, 1Click swaps settle confidentially." The swap now happens on what the changelog calls "a permissioned instance of the NEAR protocol operated by a small validator set with no public networking". The public chain shows only money going into a Treasury account and coming out again.

I tested this directly. I drew 300 successful swaps at random on each of five days and followed each one onto the chain (`src/fetch_explorer.py`, `sql/intents_swap_trace.sql`).

| Of the sampled swaps | 12 Aug | 15 Sep | 26 Oct | 28 Oct | 5 Nov |
|---|---|---|---|---|---|
| Left a public record of the swap | **98%** | 97% | 89% | 83% | **7%** |
| Went through the Treasury account | **0%** | 0% | 0% | 6% | **87%** |

In my samples the change was rolled out over about a week: 6% went through the Treasury account on 28 October and 87% by 5 November.

**So usage did not drop.** The swaps did not stop; what disappeared is the public record of them. The apps that route the flow kept routing it after the switch too: 23 of the 25 big apps from August were still sending swaps (16 at least half their August volume), and large-swap volume was -4% against August.

**The timing is what misleads.** The switch came four weeks after the freeze. Anyone reading only the public chain would see volume fall after the freeze and conclude that users left because of it. The fall is in what the chain records, not in what users do. (The number of public swap events also fell in September and October, while their dollar value held; appendix A7 has the detail.) The sampled swaps were funded by normal public deposits, so this was a change in how 1Click settles, not users choosing privacy. Why NEAR Intents made the change, I cannot say.

**What it costs a holder.** The business did not shrink, but it became harder to check. The Intents volume that DefiLlama shows is read from a dataset NEAR itself publishes. Counted in dollars, public swaps were 43% of that figure in the summer and 13% from late October. I have no evidence that the reported number is wrong. But a holder can no longer verify most of it without relying on the operator.

### Part 3. But little of it reaches NEAR holders

**In one line: Intents sends back 16% as much NEAR as NEAR issues, and the amount is not growing steadily.**

A resilient business only helps a token holder if the holder gets a share. Here is the share.

NEAR issues new tokens every day, and that dilutes everyone who holds it. The fair test of Intents' value to a holder is how much of that dilution its revenue offsets.

Since February 2026, part of Intents' revenue has been swept, as NEAR, into three wallets: a buybacks wallet, a fund fed by 1Click fees and a fund fed by front-end fees. DefiLlama calls this a buyback and credits it to NEAR's holders. The wallets are public, so I read their balances for every day of the past year from NEAR's BigQuery dataset (`sql/revenue_wallets_daily.sql`).

| | |
|---|---|
| NEAR the wallets gain a day (last 28 days) | 13,571 |
| NEAR issued a day | 86,966 |
| The wallets' gain as a share of new supply | **16%** |
| Growth needed to match all of it | **about 6.4×** |

My count comes to 100.4% of the revenue DefiLlama reports for the same days, so the two sources agree on the size.

**Doesn't a buyback push the price up?** In direction, yes: buying NEAR adds demand, and holding it takes NEAR out of circulation. That is exactly what the 16% measures. The question is size. A day, over the same 28 days, at their average NEAR price of $4.46:

| A day | NEAR | Dollars |
|---|---|---|
| Bought back with Intents' revenue | 13,571 | $60k |
| Newly issued | 86,966 | $388k |
| Traded on markets | | $707.0M |

- **Against trading, it is a rounding error.** The buyback is about 0.01% of what trades each day. It cannot move the price much by itself.
- **Against new supply, it is outweighed.** NEAR issues 6.4 times more than the buyback absorbs. Not every new token is sold, but the part that is can outweigh the buying.
- **Where a buyback can move the price is expectations.** If traders expect it to grow, they price that in early. That only lasts while it does grow, which is what the Buy level below tests.

**Does Intents burn any NEAR?** A little, the way every NEAR transaction does: 70% of each gas fee is burned. The whole chain burns about 692 NEAR a day (0.8% of new supply), and Intents' transactions are only part of that. The new-supply figure above is already net of burns, so this does not change the 16%.

**It is not growing steadily.** By month, the share of new supply that came back has run from 6% (Apr 2026) to 22% (Sep 2026), with no steady rise. Revenue in dollars grew 3.9× between Mar 2026 and Oct 2026, but NEAR's price rose 3.8×, so the extra dollars bought no extra NEAR. That is the catch in any buyback: when the token goes up, the same dollars buy less of it.

### Part 4. And no rule protects even that

**In one line: none of this NEAR is paid to holders, staked or burned, and a few signers can move it.**

A small share would still be worth something if holders were sure to get it. They are not. Nothing in code sends this NEAR to holders. It sits in the three wallets, and I read from the contracts who can move it (`src/fetch_control.py`).

| Wallet | Who can move the NEAR |
|---|---|
| Buybacks wallet | 2 of 4 keys |
| 1Click fund | 2 of 4 members |
| Front-end fund | 2 of 5 members. But its policy sets the threshold for changing the fund's own rules at 1 vote (read from the contract, not tested). |

So far the signers have left it alone: the balance fell on 2 of 367 days. But that is their choice, not a rule.

### So: Hold

**In one line: a resilient business is a reason not to sell; a small share that nobody guarantees is a reason not to buy more.**

The price is what makes the small share matter. NEAR's market value is 213 times a year of Intents' revenue, so the price already assumes years of growth. The table shows the change in NEAR's price by the end of 2029, given how fast Intents revenue grows and what multiple of revenue the market still pays. It is arithmetic, not a forecast. Supply keeps growing in every cell, which is why the price slips even where nothing else changes.

| Intents revenue growth a year | Multiple falls to a quarter (53×) | Multiple halves (107×) | Multiple holds (213×) |
|---|---|---|---|
| 0% | -76% | -52% | -5% |
| 50% | -15% | +70% | +241% |
| 100% | +110% | +321% | +742% |

A holder loses wherever growth stops, and gains only if revenue compounds and the market keeps paying a high multiple for it. That is why a resilient business is not enough for a Buy. And because the business did come through a freeze and a hack, there is no case to sell either. So: Hold.

**Why "keep it staked".** New NEAR goes to stakers. By the end of 2029, a holder who does not stake owns 7.4% less of the supply at today's issuance. A holder who stakes owns 7.3% more, before the validator's fee.

## Evidence against

- **I changed the rating a day before submitting.** I timestamped Long, which is this rule's Buy, on 10 November. On 11 November I measured the wallets and moved to Hold. I set the Buy level after seeing the data, so the fact that it fits the past proves nothing. Only the five dated predictions below test it.
- **Hold is close to Avoid.** The rule watches three warning measures, called tripwires and listed below. One is already broken: Zcash held on Intents, the balances of the users most exposed to a freeze, fell past its limit. Another holds by about a point: Intents' volume over the latest 28 days against what rival venues' volumes predict (-34.5% against a limit of -35.7%). That compares Intents with rivals, not with its own past, so it is a different measure from the -5% in Part 1.
- **The test I planned in advance was inconclusive.** It compares Intents' reported volume, over the 28 days from the freeze, with a model built from rival venues. It could only detect a loss larger than 35.7%. It found -24.3% or +1.0%, depending on which rival venues I compare with, and neither can be told from noise. Part 1 rests on the direct counts, not on this test.
- **Part of the good news comes from the operator's own data.** The swap counts in Parts 1 and 2 come from NEAR Intents' Explorer API. It is a second source, but not an independent one.
- **The bull has a real point that my rule ignores.** NEAR's governance has passed a cut in maximum issuance from 2.5% to 1.6% over 24 months (HSP-029). At that rate the same inflow would cover 24% of new supply instead of 16%. The Buy level is fixed in NEAR a day so that this cannot trigger a Buy by itself: it says nothing about whether Intents sends more to NEAR.
- **It is four weeks, and one business.** Four weeks after a shock is not the long term. And this judges NEAR by its largest measurable business. NEAR AI Cloud and other lines are not measured here; if value reaches holders through them, this thesis does not see it.

The full list, with every number, is in the appendix (B6).

## What would change my mind

The rating follows a rule, computed on every build (`src/build.py`).

| Rating | When | Now |
|---|---|---|
| **Buy** | The wallets gain 21,700 NEAR a day or more (25% of new supply), averaged over three full months | 15,486 a day (18%) |
| **Hold** | Otherwise | **Hold** |
| **Avoid** | The three wallets hold less NEAR than 28 days earlier, or two of three tripwires break (order flow against rivals, the fee Intents earns per dollar, Zcash held on Intents) | Wallets growing; 1 of 3 tripwires broken |

Five dated calls, scored only on data after 11 November 2026 and resolved on 31 March 2027. Three are about the business (P1 to P3) and two about the wallets (C1 and C2).

| | The call | If it fails |
|---|---|---|
| P1 | The flow stays above its limit against rival venues | Trust shocks or rivals are taking share |
| P2 | Intents sets a new monthly volume record, above September's | Growth has stalled |
| P3 | The fee Intents earns per dollar holds | It is buying volume with price |
| C1 | The wallets keep their NEAR | It is a treasury being spent, not a buyback |
| C2 | The wallets reach 21,700 NEAR a day over three months. This is a test, not a forecast: if it is met, the rule says Buy | What reaches NEAR is not growing fast enough to matter, and Hold stands |

Three things are outside the rule, and I would review the rating if any happened:

- **The signers commit the NEAR by a rule in code**: burned, staked, or paid to holders. That would give holders a share that is guaranteed, and it is the one change that needs no growth at all.
- **swapkit's share falls by half** with no other app replacing it.
- **NEAR Intents stops publishing 1Click swaps** through its Explorer. Reported volume would then be uncheckable.

## Check it yourself

```bash
make         # rebuilds every number, this file and the dashboard data from data/raw/ (offline, no keys)
make test    # checks on the data, the method and the outputs
make check   # confirms the rebuild reproduces the committed thesis
```

**What was fixed in advance, and what was not.** The study of the freeze and the exploit, with its tests and decision rules, was written down in advance. That file is timestamped in a Bitcoin block mined 29 minutes after the data download began, so the timestamp shows the plan was frozen early, not that it came before the data. Parts 1 to 3 were added after seeing results. The appendix lists every deviation (B7) and the event study in full (Part A).

**Sources.** NEAR's public BigQuery dataset (wallet balances, supply, every transaction to `intents.near`). The NEAR Intents Explorer API (1Click swaps). DefiLlama (reported volume and revenue, rival venues). CoinGecko (prices). NEAR Intents' changelog and NEAR's governance forum. The contracts themselves, over a public RPC endpoint. Links, fetch times and file hashes are in `data/raw/MANIFEST.json`; the incident timeline and its sources are in the appendix.
