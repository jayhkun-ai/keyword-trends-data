#!/usr/bin/env python3
"""Convert Google Trends 0-100 index readings into share-of-peak percentages.

Google Trends normalises each series so the busiest week in the chosen window
equals 100. That 100 is window-specific: it is NOT search volume and is NOT
comparable across different date ranges. This script makes the arithmetic
explicit so a reading of 20 can be stated precisely ("20% as searched as the
busiest week of this window").

It also separates the unfinished trailing week. Trends exports carry an
`isPartial` column, and the last row is commonly partial. Averaging that row in
with complete weeks changes the numbers you would quote, so both blocks are
printed and you have to say which one you used.

Standard library only.

Usage:
    python share_of_peak.py data/keyword_trends_us_12m.csv

Input: CSV with a header; column 1 is the date, column 2 the numeric index, and
an optional column named isPartial (matched case-insensitively).
Output: per-week share of peak, then two summary blocks.
"""

import csv
import sys


def load(path):
    """Return (rows_in_file_order, set_of_partial_dates).

    rows is a list of (date, value). Rows that do not parse as a number are
    skipped rather than guessed.
    """
    with open(path, newline="", encoding="utf-8-sig") as f:
        raw = list(csv.reader(f))
    if not raw:
        return [], set()

    header = [c.strip().lower() for c in raw[0]]
    partial_col = header.index("ispartial") if "ispartial" in header else None

    rows = []
    partial = set()
    for r in raw[1:]:
        if len(r) < 2:
            continue
        try:
            value = float(r[1])
        except ValueError:
            continue
        rows.append((r[0], value))
        if (
            partial_col is not None
            and len(r) > partial_col
            and r[partial_col].strip().lower() == "true"
        ):
            partial.add(r[0])
    return rows, partial


def block(label, rows):
    """Print mean / first4 / last4 for one subset of rows."""
    vals = [v for _, v in rows]
    if not vals:
        print(f"{label}: no rows")
        return
    mean = sum(vals) / len(vals)
    first4 = sum(vals[:4]) / min(4, len(vals))
    last4 = sum(vals[-4:]) / min(4, len(vals))
    ratio = (first4 / last4) if last4 else float("inf")
    print(
        f"{label}: n={len(vals)} mean={mean:.2f} "
        f"first4={first4:.2f} last4={last4:.2f} first4/last4={ratio:.2f}x"
    )


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python share_of_peak.py <input.csv>")

    rows, partial_dates = load(sys.argv[1])
    if not rows:
        sys.exit("No numeric readings found in that file.")

    peak = max(v for _, v in rows)
    peak_date = next(d for d, v in rows if v == peak)
    complete = [(d, v) for d, v in rows if d not in partial_dates]

    print(f"rows = {len(rows)}  partial rows = {len(partial_dates)}")
    print(f"peak index = {peak:.0f} (week of {peak_date})")
    if complete:
        low = min(v for _, v in complete)
        low_date = next(d for d, v in complete if v == low)
        print(f"low index = {low:.0f} (week of {low_date}, complete weeks only)")
    if partial_dates:
        print(f"partial rows excluded from the low: {', '.join(sorted(partial_dates))}")
    print()

    print("date,index,share_of_peak_pct,partial")
    for date, v in rows:
        pct = 100.0 * v / peak if peak else 0.0
        flag = "True" if date in partial_dates else "False"
        print(f"{date},{v:.0f},{pct:.2f},{flag}")

    print()
    print("Two blocks are printed on purpose: they differ only by whether the")
    print("unfinished week is included, and that choice changes the ratio you quote.")
    block("as-exported (partial week included)", rows)
    block("complete weeks only (partial dropped)", complete)
    print()
    print("share_of_peak_pct = 100 * week_index / peak_index")
    print("The index is a share of the busiest week in THIS window, not a search count.")


if __name__ == "__main__":
    main()
