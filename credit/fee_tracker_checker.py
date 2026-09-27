"""Recompute every fee in a fee tracker CSV and flag likely data-entry mistakes.

Usage:
    python credit/fee_tracker_checker.py credit/sample_fee_tracker.csv
    python credit/fee_tracker_checker.py tracker.csv --out checked.csv

Expected columns (header names must match; extra columns are ignored):
    fee_id, deal, lender, fee_type, commitment, drawn, rate_bps,
    flat_amount, start_date, end_date, day_count, lender_share_pct,
    amount_entered

fee_type values and how the expected amount is computed:
    unused       (commitment - drawn) * rate * days / basis
    ticking      (commitment - drawn) * rate * days / basis
    lc           drawn (LC face) * rate * days / basis
    interest     drawn * rate * days / basis   (rate_bps = base + spread)
    upfront      commitment * rate
    amendment    commitment * rate              (commitment = consenting hold)
    prepayment   drawn * rate                   (drawn = amount prepaid)
    agency       flat_amount * days / basis     (annual fee, accrued)
    flat         flat_amount

rate_bps is always in basis points (37.5 = 0.375%).
lender_share_pct is the lender's pro rata share (12.5 = 12.5%); blank = 100.
Days are counted start-inclusive, end-exclusive (Jan 1 -> Apr 1 = 90 days).
Stdlib only, so it runs without installing anything. Export Excel to CSV first.
"""

import argparse
import csv
import sys
from collections import defaultdict
from datetime import date, datetime

ACCRUING = {"unused", "ticking", "lc", "interest", "agency"}
ONE_TIME = {"upfront", "amendment", "prepayment", "flat"}
TOLERANCE = 0.01  # dollars


def parse_num(value):
    if value is None:
        return None
    value = str(value).strip().replace(",", "").replace("$", "")
    if value == "":
        return None
    if value.startswith("(") and value.endswith(")"):
        value = "-" + value[1:-1]
    return float(value)


def parse_date(value):
    value = (value or "").strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%d-%b-%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def day_basis(day_count):
    dc = (day_count or "ACT/360").strip().upper()
    if dc in ("ACT/365", "A/365", "365"):
        return 365
    return 360


def expected_amount(row, days, basis, *, override_drawn=None):
    """Gross fee before lender share. Returns None if inputs are missing."""
    fee_type = row["fee_type"]
    commitment = row["commitment"]
    drawn = row["drawn"] if override_drawn is None else override_drawn
    rate = row["rate_bps"] / 10_000 if row["rate_bps"] is not None else None
    flat = row["flat_amount"]

    if fee_type in ("unused", "ticking"):
        return (commitment - (drawn or 0)) * rate * days / basis
    if fee_type in ("lc", "interest"):
        return drawn * rate * days / basis
    if fee_type in ("upfront", "amendment"):
        return commitment * rate
    if fee_type == "prepayment":
        return drawn * rate
    if fee_type == "agency":
        return flat * days / basis
    if fee_type == "flat":
        return flat
    return None


def required_fields(fee_type):
    if fee_type in ("unused", "ticking"):
        return ["commitment", "rate_bps"]
    if fee_type in ("lc", "interest", "prepayment"):
        return ["drawn", "rate_bps"]
    if fee_type in ("upfront", "amendment"):
        return ["commitment", "rate_bps"]
    if fee_type in ("agency", "flat"):
        return ["flat_amount"]
    return []


def close(a, b, rel=1e-6):
    """Equal to the cent, allowing for rounding of the entered amount."""
    return abs(a - b) <= max(TOLERANCE + 0.005, abs(b) * rel)


def diagnose(row, entered, expected, days, basis, share):
    """Try known error patterns; return a list of (flag, explanation)."""
    hits = []
    for factor, label in ((100, "OFF_BY_100x"), (10_000, "OFF_BY_10000x")):
        if close(entered, expected * factor) or close(entered, expected / factor):
            hits.append((label, "bps vs % confusion (check rate_bps units)"))

    if row["fee_type"] in ACCRUING:
        alt_basis = 365 if basis == 360 else 360
        if close(entered, expected * basis / alt_basis):
            hits.append(("DAYCOUNT_365_vs_360",
                         f"amount matches ACT/{alt_basis}; tracker says ACT/{basis}"))
        for d in (days - 1, days + 1):
            if d > 0 and close(entered, expected * d / days):
                hits.append(("OFF_BY_ONE_DAY",
                             f"amount matches {d} days instead of {days} "
                             "(inclusive/exclusive date error)"))

    if row["fee_type"] in ("unused", "ticking") and row["drawn"]:
        full = expected_amount(row, days, basis, override_drawn=0) * share
        if close(entered, full):
            hits.append(("USED_FULL_COMMITMENT",
                         "fee charged on full commitment, not undrawn amount"))

    if share != 1 and close(entered, expected / share):
        hits.append(("SHARE_NOT_APPLIED",
                     "amount is the full facility fee; lender share not applied"))

    diff_cents = round(abs(entered - expected) * 100)
    if diff_cents and diff_cents % 9 == 0:
        e, x = f"{entered:.2f}", f"{expected:.2f}"
        if sorted(e) == sorted(x):
            hits.append(("TRANSPOSITION",
                         f"same digits, different order ({e} vs {x})"))
    return hits


def load(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = []
        for i, raw in enumerate(reader, start=2):  # row 1 is the header
            raw = {k.strip().lower(): (v or "").strip() for k, v in raw.items() if k}
            rows.append((i, raw))
    return rows


def check(path):
    results = []
    seen = defaultdict(list)
    share_totals = defaultdict(float)

    for line, raw in load(path):
        flags = []
        row = {
            "fee_id": raw.get("fee_id", ""),
            "deal": raw.get("deal", ""),
            "lender": raw.get("lender", ""),
            "fee_type": raw.get("fee_type", "").lower(),
        }
        try:
            for col in ("commitment", "drawn", "rate_bps", "flat_amount",
                        "lender_share_pct", "amount_entered"):
                row[col] = parse_num(raw.get(col))
        except ValueError as exc:
            flags.append(("BAD_NUMBER", str(exc)))
            results.append((line, row, None, flags))
            continue

        if row["fee_type"] not in ACCRUING | ONE_TIME:
            flags.append(("UNKNOWN_FEE_TYPE", f"'{row['fee_type']}'"))
            results.append((line, row, None, flags))
            continue

        missing = [c for c in required_fields(row["fee_type"]) if row[c] is None]
        if row["amount_entered"] is None:
            missing.append("amount_entered")
        if missing:
            flags.append(("MISSING_FIELD", ", ".join(missing)))

        start, end = parse_date(raw.get("start_date")), parse_date(raw.get("end_date"))
        days = 0
        if row["fee_type"] in ACCRUING:
            if not start or not end:
                flags.append(("BAD_DATES", "start/end date missing or unreadable"))
            elif end <= start:
                flags.append(("BAD_DATES", f"end {end} is not after start {start}"))
            else:
                days = (end - start).days

        if (row["commitment"] is not None and row["drawn"] is not None
                and row["drawn"] > row["commitment"]
                and row["fee_type"] in ("unused", "ticking")):
            flags.append(("DRAWN_GT_COMMITMENT",
                          f"drawn {row['drawn']:,.0f} > commitment {row['commitment']:,.0f}"))

        share_pct = row["lender_share_pct"] if row["lender_share_pct"] is not None else 100.0
        share = share_pct / 100
        key = (row["deal"], row["fee_type"], row["rate_bps"],
               raw.get("start_date"), raw.get("end_date"))
        dup_key = key + (row["lender"], row["amount_entered"])
        if not seen[dup_key]:  # count a duplicated row's share only once
            share_totals[key] += share_pct
        seen[dup_key].append(row["fee_id"] or f"line {line}")

        expected = None
        blocking = {"MISSING_FIELD", "BAD_DATES"}
        if not any(f[0] in blocking for f in flags):
            basis = day_basis(raw.get("day_count"))
            expected = round(expected_amount(row, days, basis) * share, 2)
            entered = row["amount_entered"]
            if not close(entered, expected):
                hits = diagnose(row, entered, expected, days, basis, share)
                flags.extend(hits or [("MISMATCH",
                                       "no known pattern; re-check the source document")])
        results.append((line, row, expected, flags))

    for ids in seen.values():
        if len(ids) > 1:
            for line, row, _, flags in results:
                if (row["fee_id"] or f"line {line}") in ids:
                    flags.append(("DUPLICATE", "also entered as " +
                                  ", ".join(i for i in ids if i != (row["fee_id"] or f"line {line}"))))

    for key, total in share_totals.items():
        if total > 100.0001:
            deal, fee_type, rate = key[0], key[1], key[2]
            for line, row, _, flags in results:
                if (row["deal"], row["fee_type"], row["rate_bps"]) == (deal, fee_type, rate):
                    flags.append(("SHARE_OVER_100",
                                  f"{deal} {fee_type} shares sum to {total:g}%"))
    return results


def fmt(x):
    return "" if x is None else f"{x:,.2f}"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("csv_path")
    ap.add_argument("--out", help="write a copy of the tracker with expected/flags columns")
    args = ap.parse_args(argv)

    results = check(args.csv_path)
    problems = [r for r in results if r[3]]

    print(f"Checked {len(results)} rows: {len(results) - len(problems)} OK, "
          f"{len(problems)} flagged\n")
    for line, row, expected, flags in problems:
        print(f"line {line}  {row['fee_id']}  {row['deal']}  {row['lender']}  "
              f"{row['fee_type']}")
        print(f"    entered {fmt(row.get('amount_entered')):>15}   "
              f"expected {fmt(expected):>15}")
        for flag, why in flags:
            print(f"    - {flag}: {why}")
        print()

    if args.out:
        with open(args.csv_path, newline="", encoding="utf-8-sig") as f:
            original = list(csv.reader(f))
        by_line = {line: (expected, flags) for line, _, expected, flags in results}
        with open(args.out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(original[0] + ["expected_amount", "flags"])
            for i, rec in enumerate(original[1:], start=2):
                expected, flags = by_line.get(i, (None, []))
                w.writerow(rec + [fmt(expected), "; ".join(fl for fl, _ in flags)])
        print(f"Wrote {args.out}")

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
