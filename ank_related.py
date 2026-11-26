#!/usr/bin/env python3
"""Rank related queries from data/related_queries.csv and print a markdown table.

The CSV is long format: seed_query, list (top|rising), related_query, value.
`value` means different things per list, and this script keeps them apart:

  * top    -> relative interest, 0-100, scaled against the peak query in that
              same seed's top list. It is a share of a peak, not a search count.
  * rising -> percent growth versus the earlier half of the same window.
              Google renders a breakout as "Breakout"; the CSV stores it as -1
              because the growth is unbounded. This script prints those as
              "Breakout" instead of inventing a number.

Standard library only.

Usage:
    python rank_related.py data/related_queries.csv
    python rank_related.py data/related_queries.csv --seed "keyword trends" --list top
"""

import argparse
import csv
import sys
from collections import defaultdict


BREAKOUT = -1


def load(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("csv_path")
    p.add_argument("--seed")
    p.add_argument("--list", dest="list_name", choices=["top", "rising"])
    p.add_argument("--limit", type=int, default=0, help="0 = no limit")
    a = p.parse_args()

    rows = load(a.csv_path)
    if not rows:
        sys.exit("CSV has no rows.")

    buckets = defaultdict(list)
    for r in rows:
        if a.seed and r["seed_query"] != a.seed:
            continue
        if a.list_name and r["list"] != a.list_name:
            continue
        buckets[(r["seed_query"], r["list"])].append((r["related_query"], int(r["value"])))

    if not buckets:
        sys.exit("No rows matched those filters.")

    for (seed, list_name), items in buckets.items():
        items.sort(key=lambda x: (-x[1], x[0]))
        if a.limit:
            items = items[: a.limit]
        unit = "relative interest (0-100, peak = 100)" if list_name == "top" else "growth vs earlier half of window"
        print(f"### `{seed}` — {list_name} ({unit})")
        print()
        print("| # | query | value |")
        print("|---:|---|---:|")
        for i, (q, v) in enumerate(items, 1):
            shown = "Breakout" if (list_name == "rising" and v == BREAKOUT) else (f"+{v}%" if list_name == "rising" else str(v))
            print(f"| {i} | {q} | {shown} |")
        print()


if __name__ == "__main__":
    main()
