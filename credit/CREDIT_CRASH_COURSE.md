# Credit Crash Course

A fast, practical guide for someone starting a credit job who needs to
(1) do the calculations, (2) write the "so what", (3) take notes in credit
meetings, and (4) key and fix fee trackers.

Read sections 1–4 first. Keep section 8 (cheat sheet) open at your desk.

---

## 1. The credit mindset in one paragraph

An equity investor asks *"how much can this company grow?"*. A lender asks
*"will I get my money back, on time, and what happens if things go wrong?"*.
Upside is capped (you earn interest plus fees, never more), but you can lose
all of your principal. So credit is about the **downside**: how much cash the business
generates, how much debt sits ahead of you, what the assets are worth if it
breaks, and what protections (covenants, collateral, guarantees) you have.

Every credit discussion comes back to three questions:

1. **Capacity to pay** – does cash flow cover interest and required principal?
2. **Leverage / cushion** – how much debt relative to earnings and asset value?
3. **Recovery** – if it defaults, where do we sit and what do we get back?

---

## 2. Core vocabulary

| Term | What it means |
|---|---|
| **Principal / par** | The amount borrowed. Prices are quoted as % of par (99.5 = 99.5 cents per $1). |
| **Revolver (RCF)** | A credit line the borrower can draw, repay, and redraw. It has a *commitment* (max size), a *drawn* balance, and an *undrawn/unused* portion. |
| **Term loan (TL)** | Funded in full at closing, repaid over time or at maturity. TLA = amortizing, bank-held; TLB = little amortization (usually 1%/yr), institutional. |
| **Delayed draw term loan (DDTL)** | Committed term loan that can be drawn later (e.g., for acquisitions). Usually carries a ticking fee until drawn. |
| **Senior secured / 1st lien** | First claim on collateral. Highest recovery, lowest spread. |
| **2nd lien / subordinated / mezz** | Paid after senior debt. Higher spread to compensate for lower recovery. |
| **Unitranche** | One loan combining senior + junior risk, common in private credit. |
| **SOFR** | The floating base rate (replaced LIBOR). Loan rate = SOFR + spread. |
| **Spread / margin** | Premium over the base rate, in basis points (e.g., S+475). |
| **Floor** | Minimum base rate. If SOFR = 0.50% and floor = 1.00%, use 1.00%. |
| **Basis point (bp)** | 1/100th of 1%. 100 bps = 1.00% = 0.01. **This is where most mistakes happen.** |
| **OID** | Original issue discount. The loan is funded below par (e.g., 98) so the lender earns the 2 points up front. |
| **Covenant** | Promise in the credit agreement. *Maintenance* = tested every quarter (e.g., leverage ≤ 5.0x). *Incurrence* = tested only when the borrower does something (borrows more, pays a dividend). |
| **Cov-lite** | No maintenance covenants (common in TLBs). |
| **Headroom / cushion** | How far the borrower is from breaching a covenant. |
| **EBITDA addbacks** | Adjustments that increase EBITDA (synergies, one-time costs). Watch these; they inflate capacity. |
| **Amortization** | Scheduled principal repayment. |
| **Sweep** | Mandatory prepayment from excess cash flow or asset sales. |
| **PIK** | Payment-in-kind: interest added to principal instead of paid in cash. A warning sign if elected by a stressed borrower. |
| **Waterfall** | Order in which cash is applied (fees → interest → principal, senior before junior). |
| **Agent** | The bank that administers the loan: collects payments, distributes to lenders, tracks fees. |
| **Pro rata** | Split in proportion to each lender's share of the facility. |

---

## 3. The ratios you will calculate constantly

Use **LTM** (last twelve months) numbers unless told otherwise.
LTM = most recent fiscal year + year-to-date current − year-to-date prior.

### Leverage (how much debt vs. earnings)

```
Total Leverage      = Total Debt / EBITDA
Senior Leverage     = Senior Secured Debt / EBITDA
Net Leverage        = (Total Debt − Cash) / EBITDA
```

Rough reading (varies by industry and sponsor):
- < 2.0x  low / investment-grade-like
- 2–4x    moderate
- 4–6x    typical leveraged loan / private credit
- > 6x    aggressive; small EBITDA misses cause big problems

### Coverage (can they pay the interest?)

```
Interest Coverage   = EBITDA / Cash Interest Expense
FCCR (fixed charge) = (EBITDA − Capex − Cash Taxes) / (Cash Interest + Scheduled Principal)
DSCR (debt service) = Cash Flow Available for Debt Service / (Interest + Principal)
```

- Interest coverage < 2.0x gets tight; < 1.5x is stressed; < 1.0x means
  EBITDA doesn't cover interest.
- FCCR/DSCR covenants are often set at 1.10x–1.25x minimum.

### Cash flow and cushion

```
Free Cash Flow (FCF)     = Cash from Operations − Capex
FCF / Debt               = % of debt that could be repaid per year
Liquidity                = Cash + Undrawn Revolver
Loan-to-Value (LTV)      = Debt / Enterprise Value (or collateral value)
EBITDA cushion to covenant = 1 − (Current Leverage / Covenant Leverage)
```

**EBITDA cushion** is the best number for writing implications. For example:
Debt = $500m, EBITDA = $100m, so leverage is 5.0x. The covenant is 6.0x.
EBITDA can fall to 500 / 6.0 = $83.3m before a breach, a **16.7% cushion**.

### Interest rate math

```
All-in rate  = max(SOFR, floor) + spread
Interest     = Principal × All-in rate × Days / 360    (ACT/360 for most USD loans)
Yield on OID ≈ spread + (OID points / expected life in years)
```

Example: $100m TL at S+500, 1% floor, SOFR 4.30%, 90-day period:
`100,000,000 × (4.30% + 5.00%) × 90/360 = $2,325,000`.

Run it yourself: `python credit/credit_metrics.py --help`

---

## 4. Fees: what they are and how they are calculated

Fee trackers are where junior people earn trust or lose it fast. Know each
fee's **basis** (what amount it's charged on), its **rate**, its **accrual
period**, and its **day count**.

| Fee | Basis | Formula | Watch out for |
|---|---|---|---|
| **Upfront / closing fee** | Commitment (or funded amount) | `Commitment × rate` | One-time. Allocated pro rata to lenders by their hold. |
| **OID** | Funded principal | `Principal × (100 − price)/100` | 98.0 = 2 points = 2%. Not a cash fee, it's a funding discount. |
| **Commitment / unused fee** | **Undrawn** revolver | `(Commitment − Drawn) × rate × days/360` | Use the **unused** amount, not the full commitment. If the drawn balance changes mid-period, split the period. Letters of credit usually count as *used*. |
| **Ticking fee** | Undrawn DDTL / committed but unfunded | `Unfunded × rate × days/360` | Often steps up over time (e.g., 0 bps for 30 days, then 50% of margin, then 100%). |
| **Letter of credit (LC) fee** | Face amount of issued LCs | `LC amount × margin × days/360` | Plus a separate **fronting fee** (e.g., 12.5 bps) paid only to the issuing bank. |
| **Agency / admin fee** | Flat | e.g., `$50,000/yr`, often paid quarterly | Paid to the agent only, not shared with lenders. |
| **Amendment / consent fee** | Holdings of **consenting** lenders | `Consenting lender's position × rate` | Non-consenting lenders don't get it. |
| **Prepayment / call premium** | Amount prepaid | `Prepaid amount × premium` (e.g., 102 → 2%) | Steps down over time ("102/101" = 2% in year 1, 1% in year 2). Soft call applies only to repricings. |
| **Exit fee** | Principal repaid | `Principal × rate` | Common in venture / asset-based lending. |
| **Default interest** | Overdue amount | Usually +200 bps on top of the normal rate | Only triggers after an event of default. |

### Day-count conventions

- **ACT/360**: actual days ÷ 360. Standard for USD loans and fees (SOFR).
- **ACT/365**: actual days ÷ 365. Used for GBP (SONIA) loans and some others.
- **30/360**: every month is treated as 30 days. Common for bonds.

Using 365 instead of 360 understates a fee by 1.4% (360/365 = 0.9863).
If a fee is off by about 1.4%, the day count is probably wrong.

**Counting days:** most loan docs count the start date and not the end
date, so Jan 1 to Apr 1 = 90 days (91 in a leap year). Check what your
tracker's convention is and apply it consistently.

### Fee worked examples

1. **Unused fee.** $50m revolver, $20m drawn, 37.5 bps unused fee, Q1 (90 days):
   `(50m − 20m) × 0.00375 × 90/360 = $28,125`
2. **Split period.** Same revolver, but $20m drawn for the first 40 days
   and $35m drawn for the last 50 days:
   `30m × 0.00375 × 40/360 + 15m × 0.00375 × 50/360 = 12,500 + 7,812.50 = $20,312.50`
3. **Pro rata upfront fee.** $200m TL, 1.00% upfront, our hold is $25m (12.5%):
   `200m × 1.00% × 12.5% = $250,000` (same as `25m × 1.00%`)
4. **LC fee + fronting.** $5m LC outstanding, S+300 margin (the LC fee is
   usually the spread only), 12.5 bps fronting, 91 days:
   LC fee `5m × 3.00% × 91/360 = $37,916.67`;
   fronting `5m × 0.125% × 91/360 = $1,579.86`

---

## 5. Writing implications: the "so what"

A number alone is useless. Every calculation you report needs three parts:

> **What happened → why it matters to us as lender → what we should do or watch.**

### Template

> [Metric] [moved from X to Y] [because of driver]. This [increases/reduces]
> [risk type: repayment / covenant / refinancing / recovery] because [link to
> our position]. [Recommendation / what to monitor / what to ask management].

### Examples

**Weak:**
"Leverage increased to 5.8x."

**Strong:**
"Total leverage rose to 5.8x from 5.1x last quarter, driven by a 12% EBITDA
decline at the industrial segment rather than new debt. Against the 6.25x
maintenance covenant this leaves ~7% EBITDA cushion (vs. 18% last quarter),
so one more quarter of similar decline would trigger a breach. We should
request a monthly flash report and understand management's cost actions
before the Q3 test date."

**Weak:**
"Interest coverage is 1.9x."

**Strong:**
"Interest coverage fell to 1.9x (from 2.6x) as the floating-rate term loan
repriced higher with SOFR. The business still covers interest, but FCF after
debt service is now ~$4m against $15m of capex planned for next year, which
implies revolver reliance. Liquidity of $38m (cash $8m + $30m undrawn RCF)
covers ~2.5 years of that shortfall, so this is a monitoring item, not a
near-term default risk."

### Words that signal direction (use them precisely)

- Risk up: *deteriorated, compressed, tightened, eroded, elevated, stretched*
- Risk down: *improved, de-levered, expanded cushion, strengthened, ample*
- Neutral: *in line with, stable, consistent with underwriting case*

Always compare to **something**: last quarter, the underwriting (base) case,
covenant levels, peers, or budget. "Versus underwriting" is what credit
committees care about most.

### Common lender concerns to link implications to

- Covenant headroom
- Liquidity runway (cash + revolver ÷ cash burn)
- Refinancing risk (maturity wall, what leverage would be refinanced at)
- Collateral / recovery value
- Sponsor support (will the PE owner put in more equity?)
- Customer concentration, margin trends, working capital swings
- Quality of EBITDA (addbacks as % of EBITDA; > 20–25% is a flag)

---

## 6. Taking notes in credit meetings

Use `credit/templates/credit_meeting_notes.md`. Tips:

1. **Capture decisions and action items first**, discussion second. If you
   only get one thing down, get "who does what by when".
2. **Write numbers exactly as said**, with units: "EBITDA $42.3m LTM",
   not "EBITDA ~42".
3. **Mark who said it** for opinions and concerns ("JS: worried about
   customer concentration, top 3 = 48% of revenue").
4. **Flag open questions** with `[?]` and look them up after, don't interrupt.
5. **Use shorthand consistently**: `↑ ↓ →`, `lev`, `cov`, `RCF`, `TL`,
   `LTM`, `YoY`, `bps`, `mgmt`, `spons`, `AI` (action item).
6. **Clean up within an hour** while you still remember, then send to
   the deal lead for a sanity check before it goes wider.
7. Listen for these phrases. They usually lead to action items:
   "can we get…", "let's confirm…", "subject to…", "I'd want to see…",
   "condition of approval…".

### What typically gets discussed

- Deal/borrower overview and purpose of the loan
- Sources & uses, pro forma capital structure
- Financial performance vs. budget/underwriting
- Key credit metrics and covenant compliance
- Risks and mitigants
- Structure: pricing, fees, covenants, collateral
- Recommendation and vote / approval conditions

---

## 7. Fee tracker workflow: key fast, then fix

You are doing mass entry and then correcting. Do it in two passes:

**Pass 1: Entry (speed).** Enter exactly what the source documents say
(agent notices, fee letters, credit agreement). Don't calculate in your head.
Record the source doc for every line.

**Pass 2: Check (accuracy).** Run the checker:

```bash
python credit/fee_tracker_checker.py credit/sample_fee_tracker.csv
```

It recomputes every fee from its inputs and flags:

| Flag | Likely cause |
|---|---|
| `OFF_BY_100x` / `OFF_BY_10000x` | bps vs. % confusion (50 bps typed as 50%, or as 0.5 bps) |
| `DAYCOUNT_365_vs_360` | Wrong day-count basis (~1.4% difference) |
| `TRANSPOSITION` | Two digits swapped (difference divisible by 9) |
| `USED_FULL_COMMITMENT` | Unused fee charged on full commitment instead of undrawn |
| `OFF_BY_ONE_DAY` | Start/end date inclusive vs. exclusive error |
| `DUPLICATE` | Same fee entered twice |
| `BAD_DATES` | End date before start date or missing |
| `MISSING_FIELD` | Required input blank |
| `SHARE_OVER_100` | Lender shares on a fee sum to more than 100% |
| `MISMATCH` | Doesn't tie and no known pattern matched: go back to the source doc |

### Manual error-hunting tricks (useful anywhere)

- **Divisible by 9 rule:** if a total is off by an amount divisible by 9,
  you likely transposed two digits (e.g., 5,430 vs 5,340; diff = 90).
- **Half-the-difference rule:** if off by X and an entry equals X/2, that
  entry was probably entered with the wrong sign (added instead of subtracted).
- **Tie out totals:** sum of lender shares must equal the facility total;
  pro rata percentages must sum to 100%.
- **Reasonableness check:** a quarterly unused fee on a $50m revolver should
  be in the tens of thousands, not millions. Estimate first, then compare.
- **Sort and scan:** sort by amount; outliers at the top/bottom are usually
  typos.

---

## 8. Cheat sheet

```
1 bp = 0.01% = 0.0001            100 bps = 1%
50 bps on $10m for a year = $50,000
Quarter ≈ 90–92 days; ACT/360 year fraction for 91 days = 0.2528

Leverage        = Debt / EBITDA
Net leverage    = (Debt − Cash) / EBITDA
Int. coverage   = EBITDA / Interest
FCCR            = (EBITDA − Capex − Taxes) / (Interest + Sched. Principal)
EBITDA cushion  = 1 − Leverage / Covenant
Liquidity       = Cash + Undrawn RCF
Interest        = Principal × (max(SOFR, floor) + spread) × days/360
Unused fee      = (Commitment − Drawn − LCs) × rate × days/360
OID $           = Principal × (100 − price)/100
Pro rata share  = Our hold / Facility size
```

### Questions to ask yourself before sending anything

1. Did I use LTM and the right period?
2. Are units consistent ($ vs $m vs $000s)?
3. bps vs %: did I divide by 10,000 for bps?
4. 360 or 365?
5. Drawn vs. undrawn vs. commitment: which balance is the fee on?
6. Does the total tie to the agent notice / source doc?
7. Did I say *why it matters*, not just *what it is*?

---

## 9. Two-week study plan

| Days | Focus |
|---|---|
| 1–2 | Sections 1–3. Recompute every example by hand, then with the scripts. |
| 3–4 | Section 4. Rebuild all fee examples in Excel from scratch. |
| 5 | Fix every error in `sample_fee_tracker.csv` yourself **before** running the checker, then compare. |
| 6–7 | Pull a real 10-K (any leveraged company), compute leverage, coverage, FCF, liquidity. Write 3 implication paragraphs using section 5. |
| 8–9 | Read the covenant and fee sections of one credit agreement (EDGAR: search "credit agreement" exhibits, Ex-10.1). Find: facility sizes, margin, floor, unused fee, financial covenants, call protection. |
| 10 | Practice meeting notes: watch an earnings call replay and take notes using the template. |
| 11–14 | Repeat 6–7 for two more companies in your team's sectors. |

Good free resources: company 10-K/10-Q filings (SEC EDGAR), S&P / Moody's
public methodology papers (how rating agencies think about leverage),
Investopedia for definitions, and your firm's own past credit memos (the
best template for house style).
