"""Compute core credit ratios and draft plain-English implications.

Manual inputs ($ in any consistent unit, e.g. $m):
    python credit/credit_metrics.py --debt 500 --cash 40 --ebitda 100 \
        --interest 45 --capex 20 --taxes 8 --principal 5 --revolver-undrawn 50 \
        --covenant 6.0

From a public ticker's latest annual statements (needs `pip install yfinance`):
    python credit/credit_metrics.py --ticker F --covenant 4.0

Interest on a loan for one period:
    python credit/credit_metrics.py --loan 100000000 --sofr 4.30 --spread-bps 500 \
        --floor 1.00 --days 90
"""

import argparse
import sys


def loan_interest(principal, sofr_pct, spread_bps, floor_pct, days, basis=360):
    base = max(sofr_pct, floor_pct or 0) / 100
    rate = base + spread_bps / 10_000
    return rate, principal * rate * days / basis


def from_yfinance(ticker):
    try:
        import yfinance as yf
    except ImportError:
        sys.exit("yfinance is not installed: pip install yfinance")

    t = yf.Ticker(ticker)
    inc, bs, cf = t.income_stmt, t.balance_sheet, t.cashflow

    def latest(df, *names):
        for n in names:
            if df is not None and n in df.index:
                v = df.loc[n].dropna()
                if len(v):
                    return abs(float(v.iloc[0])) / 1e6
        return None

    return {
        "debt": latest(bs, "Total Debt"),
        "cash": latest(bs, "Cash And Cash Equivalents",
                       "Cash Cash Equivalents And Short Term Investments"),
        "ebitda": latest(inc, "EBITDA", "Normalized EBITDA"),
        "interest": latest(inc, "Interest Expense", "Interest Expense Non Operating"),
        "capex": latest(cf, "Capital Expenditure"),
        "taxes": latest(cf, "Income Tax Paid Supplemental Data"),
        "cfo": latest(cf, "Operating Cash Flow"),
    }


def ratios(d):
    r = {}
    debt, cash, ebitda = d.get("debt"), d.get("cash") or 0, d.get("ebitda")
    interest, capex, taxes = d.get("interest"), d.get("capex") or 0, d.get("taxes") or 0
    principal = d.get("principal") or 0

    if debt is not None and ebitda:
        r["total_leverage"] = debt / ebitda
        r["net_leverage"] = (debt - cash) / ebitda
    if ebitda and interest:
        r["interest_coverage"] = ebitda / interest
        r["fccr"] = (ebitda - capex - taxes) / (interest + principal)
    if d.get("cfo") is not None:
        r["fcf"] = d["cfo"] - capex
        if debt:
            r["fcf_to_debt"] = r["fcf"] / debt
    r["liquidity"] = cash + (d.get("revolver_undrawn") or 0)
    if d.get("covenant") and "total_leverage" in r:
        r["ebitda_cushion"] = 1 - r["total_leverage"] / d["covenant"]
        r["breach_ebitda"] = debt / d["covenant"]
    return r


def implications(r, d):
    out = []
    lev = r.get("total_leverage")
    if lev is not None:
        band = ("low" if lev < 2 else "moderate" if lev < 4
                else "typical for leveraged lending" if lev < 6 else "aggressive")
        out.append(f"Total leverage of {lev:.1f}x is {band}; net of cash it is "
                   f"{r['net_leverage']:.1f}x.")
    cushion = r.get("ebitda_cushion")
    if cushion is not None:
        tone = ("a breach today" if cushion < 0 else "very tight" if cushion < 0.10
                else "adequate" if cushion < 0.25 else "comfortable")
        out.append(f"Against the {d['covenant']:.2f}x covenant, EBITDA can fall "
                   f"{max(cushion, 0):.0%} (to {r['breach_ebitda']:,.1f}) before a breach: "
                   f"{tone}.")
    ic = r.get("interest_coverage")
    if ic is not None:
        tone = ("EBITDA does not cover interest" if ic < 1 else "stressed" if ic < 1.5
                else "tight" if ic < 2 else "adequate" if ic < 3 else "strong")
        out.append(f"Interest coverage of {ic:.1f}x is {tone}.")
    fccr = r.get("fccr")
    if fccr is not None and fccr < 1.1:
        out.append(f"FCCR of {fccr:.2f}x is below a typical 1.10x minimum: after capex, "
                   "taxes and debt service the business is using cash, so watch "
                   "revolver usage and liquidity.")
    if r.get("liquidity"):
        out.append(f"Liquidity (cash + undrawn revolver) is {r['liquidity']:,.1f}.")
    out.append("Next: compare each metric to last quarter and the underwriting case, "
               "and say what we should do or monitor.")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ticker")
    for f in ("debt", "cash", "ebitda", "interest", "capex", "taxes", "principal",
              "cfo", "revolver-undrawn", "covenant"):
        ap.add_argument(f"--{f}", type=float)
    ap.add_argument("--loan", type=float, help="principal for an interest calculation")
    ap.add_argument("--sofr", type=float, help="base rate in %% (4.30)")
    ap.add_argument("--spread-bps", type=float)
    ap.add_argument("--floor", type=float, default=0.0, help="floor in %% (1.00)")
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--basis", type=int, default=360, choices=(360, 365))
    a = ap.parse_args(argv)

    if a.loan is not None:
        if a.sofr is None or a.spread_bps is None:
            ap.error("--loan needs --sofr and --spread-bps")
        rate, amt = loan_interest(a.loan, a.sofr, a.spread_bps, a.floor, a.days, a.basis)
        print(f"All-in rate {rate:.4%} = max(SOFR {a.sofr:.2f}%, floor {a.floor:.2f}%)"
              f" + {a.spread_bps:g} bps")
        print(f"Interest = {a.loan:,.2f} x {rate:.4%} x {a.days}/{a.basis} = {amt:,.2f}")
        return

    d = from_yfinance(a.ticker) if a.ticker else {}
    for k in ("debt", "cash", "ebitda", "interest", "capex", "taxes", "principal",
              "cfo", "revolver_undrawn", "covenant"):
        v = getattr(a, k)
        if v is not None:
            d[k] = v  # manual inputs override pulled data
    if not d.get("ebitda") or d.get("debt") is None:
        ap.error("need at least --debt and --ebitda (or --ticker)")

    if a.ticker:
        print(f"{a.ticker.upper()} latest annual, $m: " +
              ", ".join(f"{k}={v:,.0f}" for k, v in d.items()
                        if v is not None and k != "covenant"))
    r = ratios(d)
    labels = {
        "total_leverage": ("Total leverage", "{:.2f}x"),
        "net_leverage": ("Net leverage", "{:.2f}x"),
        "interest_coverage": ("Interest coverage", "{:.2f}x"),
        "fccr": ("FCCR", "{:.2f}x"),
        "fcf": ("Free cash flow", "{:,.1f}"),
        "fcf_to_debt": ("FCF / debt", "{:.1%}"),
        "liquidity": ("Liquidity", "{:,.1f}"),
        "ebitda_cushion": ("EBITDA cushion to covenant", "{:.1%}"),
        "breach_ebitda": ("EBITDA at breach", "{:,.1f}"),
    }
    for k, (label, f) in labels.items():
        if k in r:
            print(f"  {label:<28}{f.format(r[k])}")
    print("\nDraft implications:")
    for line in implications(r, d):
        print(f"  - {line}")


if __name__ == "__main__":
    main()
