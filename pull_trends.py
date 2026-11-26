#!/usr/bin/env python3
"""Re-pull the datasets in this repo from Google Trends.

Every file in data/ was produced by this script or by the same calls it makes.
Nothing here is hand-edited, so re-running it should reproduce the same shape.

Requirements:
    pip install pytrends==4.9.2 pandas

Notes learned the hard way (kept here so you do not repeat them):
  * pytrends 4.9.2 with urllib3 2.x raises TypeError if you pass `retries=`.
  * Two calls back to back commonly returns 429. Sleep between calls.
  * Google Trends normalises each series per window: the busiest week in the
    window is 100. A 100 here is NOT search volume and is NOT comparable to a
    100 pulled over a different date range.

Usage:
    python pull_trends.py --keyword "keyword trends" --geo US --timeframe "today 12-m"
    python pull_trends.py --related "seo keyword research" --geo US --timeframe "today 12-m"
"""

import argparse
import sys
import time

import pandas as pd
from pytrends.request import TrendReq


def build(geo, timeframe):
    # retries deliberately omitted: see module docstring
    return TrendReq(hl="en-US", tz=0, geo=geo, timeout=(10, 25))


def pull_interest(pytrends, keyword, path):
    pytrends.build_payload([keyword], cat=0, timeframe=pytrends.timeframe, geo=pytrends.geo, gprop="")
    df = pytrends.interest_over_time()
    if df.empty:
        sys.exit("Google Trends returned no rows for this keyword/window.")
    out = df[[keyword, "isPartial"]].reset_index()
    out.columns = ["date", "index", "isPartial"]
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    out.to_csv(path, index=False)
    print(f"wrote {path}: {len(out)} rows, peak index {out['index'].max()}")


def pull_related(pytrends, keyword, path):
    pytrends.build_payload([keyword], cat=0, timeframe=pytrends.timeframe, geo=pytrends.geo, gprop="")
    tables = pytrends.related_queries().get(keyword) or {}
    rows = []
    for list_name in ("top", "rising"):
        table = tables.get(list_name)
        if table is None:
            continue
        for _, r in table.iterrows():
            rows.append([keyword, list_name, r["query"], int(r["value"])])
    if not rows:
        sys.exit("No related queries returned.")
    pd.DataFrame(rows, columns=["seed_query", "list", "related_query", "value"]).to_csv(path, index=False)
    print(f"wrote {path}: {len(rows)} rows")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--keyword", help="pull a 0-100 interest-over-time series for this term")
    p.add_argument("--related", help="pull top and rising related queries for this term")
    p.add_argument("--geo", default="US")
    p.add_argument("--timeframe", default="today 12-m")
    p.add_argument("--out")
    p.add_argument("--sleep", type=float, default=8.0, help="seconds between calls")
    a = p.parse_args()
    if not a.keyword and not a.related:
        p.error("pass --keyword or --related")

    term = a.keyword or a.related
    pytrends = build(a.geo, a.timeframe)
    pytrends.timeframe = a.timeframe
    pytrends.geo = a.geo

    if a.keyword:
        pull_interest(pytrends, a.keyword, a.out or "data/interest_over_time.csv")
        time.sleep(a.sleep)
    if a.related:
        pull_related(pytrends, a.related, a.out or "data/related_queries.csv")


if __name__ == "__main__":
    main()
