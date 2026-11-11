# Hold NEAR. Intents is a resilient business, but NEAR holders get little of what it earns so far.

*It came through a freeze and a hack with its volume intact. But only 16% of new supply comes back, none of it is paid to holders, and no rule in code protects it.*

NEAR HACKATHON 2026 · Investment Thesis track · data to 2026-11-09 · about ten minutes to read · full tables, method and caveats: [`APPENDIX.md`](APPENDIX.md)

## The claim

The case for owning NEAR now rests on one business. NEAR Intents swaps tokens across blockchains, and part of what it earns is sent back as NEAR into three wallets. NEAR's market value is 213 times a year of Intents' revenue. A price like that says two things: the business will keep growing, and holders will share in it.

I checked both against the chain. Four things came out.

- **The business held up under stress.** Within a month Intents froze users' funds and was then exploited for $3.8M. Its main product is 1Click, the swap service that apps plug into. Counted swap by swap, 1Click volume in the four weeks that followed was -5% against August.
- **Holders' claim on it is small.** The three wallets gain 13,571 NEAR a day. NEAR issues 86,966 a day. So 16% of the new supply comes back.
- **The claim is unsecured.** None of that NEAR is paid to holders, staked or burned. It sits in wallets that a few signers can move, and no rule in code says what happens to it.
- **It is getting harder to check.** Since 27 October most swaps settle off the public chain. In August 98% of the swaps I sampled left a public record. In November, 7%.

**So the rating is Hold.** Keep the NEAR you own, and keep it staked. Do not add yet. The rating turns to Buy when the wallets take in 21,700 NEAR a day, 25% of new supply, for three full months. The last three full months averaged 15,486. It turns to Avoid if the wallets shrink or the flow breaks. The rule is written down and timestamped in [`RATING.md`](RATING.md), with five dated predictions that will show by 31 March 2027 whether I was right.

## Evidence for the rating

Parts 1 and 2 are why this is not a Buy. Part 3 is why it is not an Avoid.

### Part 1. Why not Buy: little reaches NEAR, and no rule protects it

Since February 2026, part of Intents' revenue has been swept, as NEAR, into three wallets: a buybacks wallet, a fund fed by 1Click fees and a fund fed by front-end fees. DefiLlama calls this a buyback and credits it to NEAR's holders. The wallets are public, so I read their balances for every day of the past year from NEAR's BigQuery dataset (`sql/revenue_wallets_daily.sql`).

| | |
|---|---|
| NEAR held in the three wallets | 4,224,522 (0.32% of supply) |
| Gained a day, last 28 days | 13,571 NEAR |
| Issued by NEAR a day | 86,966 NEAR |
| Share of new supply that comes back | **16%** (11% without the front-end fund) |
| Paid to holders, staked or burned | **None** |

My count comes to 100.4% of the revenue DefiLlama reports for the same days, so the two sources agree on the size.

**It is not growing steadily.** By month, the share of new supply that came back has run from 6% (Apr 2026) to 22% (Sep 2026), with no steady rise. Revenue in dollars grew 3.9× between Mar 2026 and Oct 2026, but NEAR's price rose 3.8×, so the extra dollars bought no extra NEAR. That is the catch in any buyback: when the token goes up, the buyback retires less of it.

**A few signers decide what happens to it.** I read the rules from the contracts themselves (`src/fetch_control.py`).

| Wallet | Who can move the NEAR |
|---|---|
| Buybacks wallet | 2 of 4 keys |
| 1Click fund | 2 of 4 members |
| Front-end fund | 2 of 5 members. But its policy sets the threshold for changing the fund's own rules at 1 vote (read from the contract, not tested). |

Nothing in code sends this NEAR to holders. Today it is a treasury that has so far been left alone: the balance fell on 2 of 367 days.

**What the price already assumes.** The table shows the change in NEAR's price by the end of 2029, given how fast Intents revenue grows and what multiple of revenue the market still pays. It is arithmetic, not a forecast. Supply keeps growing in every cell, which is why the price slips even where nothing else changes.

| Intents revenue growth a year | Multiple falls to a quarter (53×) | Multiple halves (107×) | Multiple holds (213×) |
|---|---|---|---|
| 0% | -76% | -52% | -5% |
| 50% | -15% | +70% | +241% |
| 100% | +110% | +321% | +742% |

A holder loses wherever growth stops. A holder gains only if revenue compounds and the market keeps paying a high multiple for it. That is why this is not a Buy.

**Why "staked".** New NEAR goes to stakers. By the end of 2029, a holder who does not stake owns 7.4% less of the supply at today's issuance. A holder who stakes owns 7.3% more, before the validator's fee.

### Part 2. Why not Buy: it is getting harder to check

Until this autumn, anyone could count Intents' swaps on NEAR's public chain. On 27 October 2026 NEAR Intents' changelog said: "From October 27, 2026, 1Click swaps settle confidentially." The swap now happens on what the changelog calls "a permissioned instance of the NEAR protocol operated by a small validator set with no public networking". The public chain shows only money going into a Treasury account and coming out again.

I tested this directly. I drew 300 successful swaps at random on each of five days and followed each one onto the chain (`src/fetch_explorer.py`, `sql/intents_swap_trace.sql`).

| Of the sampled swaps | 12 Aug | 15 Sep | 26 Oct | 28 Oct | 5 Nov |
|---|---|---|---|---|---|
| Left a public record of the swap | **98%** | 97% | 89% | 83% | **7%** |
| Went through the Treasury account | **0%** | 0% | 0% | 6% | **87%** |

The swaps did not stop. What disappeared is the public record of them.

This matters because of where the headline number comes from. The Intents volume that DefiLlama shows is read from a dataset NEAR itself publishes. The table above counts swaps. Counted in dollars against DefiLlama's total, public swaps were 43% of that figure in the summer and 13% from late October. Adding the 1Click swaps that now settle privately, I can account for about 33% of it.

I have no evidence that the reported number is wrong. The point is narrower: a holder can no longer check most of it without relying on the operator. The part I can still count swap by swap, 1Click, is only part of Intents' volume, so it cannot confirm the total either way. The sampled swaps came from ordinary deposits, so this was a change in how 1Click settles, not users choosing privacy. Why NEAR Intents made the change, I cannot say.

### Part 3. Why not Avoid: the business held up through a freeze and a hack

A small claim is only worth holding if the business behind it lasts. This autumn it was tested twice.

- **2026-09-29: a freeze.** Intents' compliance system blocked more than $50M of transfers linked to the Bitget hack and froze $503k in the middle of a swap. Three weeks earlier a Zcash user had reported $589k held for 50 days.
- **2026-10-01: an exploit.** $3.8M was taken, and the contract was paused on eleven networks. The funds were returned the next day.

The bear case was simple: a venue that can freeze your money is not trustless, so users will leave the first time it does. Here is what happened to swaps of $10,000 or more, which are about three-quarters of 1Click's dollars.

| | August | 4 weeks from the freeze | After 27 Oct |
|---|---|---|---|
| Large-swap volume a day | $28.9M | $28.5M | $27.6M |
| Apps routing large swaps | 66 | 81 | 64 |
| Largest app's share of the dollars | 35% | 40% | 37% |

- **The flow stayed.** In the four weeks from the freeze, large-swap volume was -1% against August, and all 1Click volume -5%.
- **The apps stayed.** Most of this volume arrives through apps that plug Intents into their own products. Of the 25 apps that routed $1M or more in August, 17 kept at least half their volume.
- **Revenue rose in dollars.** $23k a day in August, $59k in the four weeks before the freeze, $72k in the four weeks after. In NEAR the wallets' gain was +11% against August, though below September's record.

Two cautions belong here.

- **Individual users came back less.** Of addresses that sent large swaps on five or more days before the freeze, 59% came back (94 addresses). In the one calm period I can compare with, 68% to 75% did.
- **One app carries a third of it.** Since 27 October swapkit has routed 37% of large-swap dollars. A routing decision at one company could move more volume than the freeze did.

So the customer that decides is the app, not the end user. Most apps did not leave.

## Evidence against

- **I changed the rating a day before submitting.** I timestamped Long, which is this rule's Buy, on 10 November. On 11 November I measured the wallets and moved to Hold. I set the Buy level after seeing the data, so the fact that it fits the past proves nothing. Only the five dated predictions below test it.
- **Hold is close to Avoid.** The rule watches three warning measures, called tripwires and listed below. One is already broken: Zcash held on Intents fell past its limit. Another, order flow against rival venues over the latest 28 days, holds by about a point (-34.5% against a limit of -35.7%).
- **The test I planned in advance was inconclusive.** It compares Intents' reported volume, over the 28 days from the freeze, with a model built from rival venues. It could only detect a loss larger than 35.7%. It found -24.3% or +1.0%, depending on which rival venues I compare with, and neither can be told from noise. Part 3 rests on the direct counts, not on this test.
- **Part of the good news comes from the operator's own data.** The swap-by-swap counts in Part 3 come from NEAR Intents' Explorer API. It is a second source, but not an independent one.
- **The bull has a real point that my rule ignores.** NEAR's governance has passed a cut in maximum issuance from 2.5% to 1.6% over 24 months (HSP-029). At that rate the same inflow would cover 24% of new supply instead of 16%. The Buy level is fixed in NEAR a day so that this cannot trigger a Buy by itself: it says nothing about whether Intents sends more to NEAR.
- **It is four weeks, and one business.** Four weeks after a shock is not the long term. And if value reaches NEAR holders some other way than Intents, this thesis does not see it.

The full list, with every number, is in the appendix (B6).

## What would change my mind

The rating follows a rule, computed on every build (`src/build.py`).

| Rating | When | Now |
|---|---|---|
| **Buy** | The wallets gain 21,700 NEAR a day or more (25% of new supply), averaged over three full months | 15,486 a day (18%) |
| **Hold** | Otherwise | **Hold** |
| **Avoid** | The three wallets hold less NEAR than 28 days earlier, or two of three tripwires break (order flow against rivals, the fee Intents earns per dollar, Zcash held on Intents) | Wallets growing; 1 of 3 tripwires broken |

Five predictions, scored only on data after 11 November 2026 and resolved on 31 March 2027. Three are about the business (P1 to P3) and two about the wallets (C1 and C2).

| | I predict | If I am wrong |
|---|---|---|
| P1 | The flow stays above its limit against rival venues | Trust shocks or rivals are taking share |
| P2 | Intents sets a new monthly volume record, above September's | Growth has stalled |
| P3 | The fee Intents earns per dollar holds | It is buying volume with price |
| C1 | The wallets keep their NEAR | It is a treasury being spent, not a buyback |
| C2 | The wallets reach 21,700 NEAR a day over three months | What reaches NEAR is not growing fast enough to matter, and Hold stands |

Three things are outside the rule, and I would review the rating if any happened:

- **The signers commit the NEAR by a rule in code**: burned, staked, or paid to holders. That would turn an unsecured claim into a secured one, and it is the one change that needs no growth at all.
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
