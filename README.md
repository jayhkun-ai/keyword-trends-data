# Keyword Trends Data — raw Google Trends 0-100 series

Raw, reproducible exports from Google Trends, plus small scripts that turn the 0-100 index into statements you can actually defend. Every number in `data/` came back from Google Trends through `pytrends`; nothing is estimated, smoothed, or hand-entered.

The point of this repo is one specific misunderstanding. People read a Google Trends index of 20 and say "search volume dropped 80 percent." What the 20 actually means is *20 percent as searched as the busiest week in the chosen window*. That busiest week is rebuilt to 100 every time you change the date range, so a 100 pulled last year and a 100 pulled today are not the same quantity. The scripts here make that arithmetic explicit.

## Files

| File | Rows | What it is | Where it came from |
|---|---|---|---|
| `data/keyword_trends_us_12m.csv` | 53 | Weekly index for `keyword trends`, US, `today 12-m`. Columns: `date, index, isPartial`. | Google Trends interest-over-time, pulled 2026-11-26 |
| `data/related_queries.csv` | 87 | Long-format top and rising related queries for 4 seeds: `keyword trends`, `google trends`, `keyword research`, `seo keyword research`. Columns: `seed_query, list, related_query, value`. | Google Trends related-queries, geo=US, `today 12-m`, pulled 2026-11-26 |
| `share_of_peak.py` | — | Converts index readings to share-of-peak percentages; prints peak and low week, all-week mean, first-4 vs last-4 mean. | This repo |
| `rank_related.py` | — | Ranks related queries per seed and prints markdown; keeps `top` (relative interest) and `rising` (percent growth) units separate. | This repo |
| `pull_trends.py` | — | Re-pulls the files above so you can verify them or move them to another country or window. | This repo |

No third-party packages are needed for `share_of_peak.py` or `rank_related.py`. Only `pull_trends.py` needs `pytrends`.

## What the data actually says

Direct readings from `data/keyword_trends_us_12m.csv`, produced by running the script:

```
$ python share_of_peak.py data/keyword_trends_us_12m.csv
rows = 53  partial rows = 1
peak index = 100 (week of 2026-01-18)
low index = 0 (week of 2026-08-30, complete weeks only)
partial rows excluded from the low: 2026-11-22
...
as-exported (partial week included): n=53 mean=41.26 first4=31.75 last4=11.50 first4/last4=2.76x
complete weeks only (partial dropped): n=52 mean=41.90 first4=31.75 last4=14.25 first4/last4=2.23x
```

Four things worth noticing, all traceable to those lines:

1. The peak is a single week in January. One week at 100 does not make a trend; the mean is 41.26 precisely because most weeks sit far below the peak.
2. Six **complete** weeks read 0 (2026-08-30, 2026-09-13, 2026-09-20, 2026-09-27, 2026-10-04, 2026-10-18). The trough is real. What is not real is treating the last row — 2026-11-22, flagged `isPartial = True` — as another low; it is an unfinished week.
3. The partial row is not cosmetic. Counting it makes the last-4 mean 11.50; dropping it makes the same statistic 14.25 over 52 rows. The script prints both blocks so you cannot pick one silently.
4. The first-4 vs last-4 ratio is therefore 2.76× (as exported) or 2.23× (complete weeks only). Both are defensible; publishing one without saying which is not. And both are measured against this window's own January peak — re-pull with `today 5-y` and the same calendar weeks will not carry the same numbers, because 100 moves.

## Reproduce

```sh
git clone https://github.com/<your-account>/keyword-trends-data
cd keyword-trends-data
python share_of_peak.py data/keyword_trends_us_12m.csv
python rank_related.py data/related_queries.csv --seed "keyword trends"
```

To re-pull from Google instead of trusting the committed CSV:

```sh
pip install pytrends==4.9.2 pandas
python pull_trends.py --keyword "keyword trends" --geo US --timeframe "today 12-m" --out data/check.csv
```

## Method notes and traps

These are observed failures from the actual pull, not general advice:

- `pytrends` 4.9.2 with `urllib3` 2.x: passing `retries=` to `TrendReq` raises `TypeError: __init__() got an unexpected keyword argument 'retries'`. Omit it and retry yourself.
- Two calls in one session back to back commonly returns `429 Too Many Requests`. `pull_trends.py` sleeps 8 seconds between calls by default; raise it with `--sleep` if you still get 429.
- `gprop=""` is web search. News, images, and YouTube are separate series with separate normalisations and must not be compared against each other.
- Related-queries `top` values are relative interest scaled within that seed's own top list, so the top row is always 100. `rising` values are percent growth versus the earlier half of the same window, and a breakout is stored as `-1` in the CSV because its growth is unbounded — `rank_related.py` prints those as `Breakout` instead of inventing a figure.
- `interest_over_time` returns a limited number of buckets per window. Longer ranges come back weekly or monthly depending on length; check the `date` column before assuming weekly spacing.

## Attribution

If you use these files, cite the repo and note that the underlying values are Google Trends normalised indices, not search volumes. Google Trends data is provided by Google under its own terms; this repo only republishes the normalised series that its public interface returns.

A longer written explanation of the index and of the query method is at [keywordtrendsguide.com](https://keywordtrendsguide.com/).
