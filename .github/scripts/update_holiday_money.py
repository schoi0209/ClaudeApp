#!/usr/bin/env python3
"""Refresh holiday-money-data.json.

Each series is stored newest month first. q="USDX" means units of X per 1 USD,
q="XUSD" means USD per 1 X. The file is only rewritten when every currency
downloads and passes validation, so a bad run never replaces good data.

Two modes:
- ALPHAVANTAGE_API_KEY set (repo secret): rebuild the full monthly history from
  Alpha Vantage FX_MONTHLY. The free key allows about 25 calls a day; one run uses 15.
- No key: keep the stored history and update only the current month with today's
  rate from the free, key-less currency-api (fawazahmed0). When a new month
  starts, the last stored rate of the old month stays as its close.

Local test without network: --latest-file usd.json (same shape as currency-api).
"""
import csv
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import date

OUT = "holiday-money-data.json"
PAIRS = {  # currency -> quote direction against USD
    "AUD": "XUSD", "EUR": "XUSD", "GBP": "XUSD", "NZD": "XUSD",
    "JPY": "USDX", "KRW": "USDX", "SGD": "USDX", "THB": "USDX", "IDR": "USDX",
    "VND": "USDX", "CNY": "USDX", "PHP": "USDX", "MYR": "USDX", "HKD": "USDX",
    "TWD": "USDX",
}
MIN_MONTHS = 100


def fetch(cur, q, key):
    frm, to = (cur, "USD") if q == "XUSD" else ("USD", cur)
    url = "https://www.alphavantage.co/query?" + urllib.parse.urlencode({
        "function": "FX_MONTHLY", "from_symbol": frm, "to_symbol": to,
        "datatype": "csv", "apikey": key,
    })
    for attempt in range(3):
        with urllib.request.urlopen(url, timeout=60) as r:
            text = r.read().decode("utf-8", "replace")
        if text.lstrip().startswith("timestamp"):
            break
        print(f"  {cur}: attempt {attempt + 1} not CSV: {text[:160]!r}")
        time.sleep(20)
    else:
        raise RuntimeError(f"{cur}: no CSV returned")
    rows = {}
    for row in csv.DictReader(io.StringIO(text)):
        close = float(row["close"])
        if close <= 0:
            raise RuntimeError(f"{cur}: bad close {close} on {row['timestamp']}")
        rows[row["timestamp"][:7]] = (row["timestamp"], close)  # YYYY-MM
    return rows


def prev_month(ym):
    y, m = int(ym[:4]), int(ym[5:])
    return f"{y - 1}-12" if m == 1 else f"{y}-{m - 1:02d}"


LATEST_URLS = [
    "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.min.json",
    "https://latest.currency-api.pages.dev/v1/currencies/usd.min.json",
]
MAX_JUMP = 0.15  # refuse a latest rate more than 15% away from the stored one


def fetch_latest():
    last = None
    for url in LATEST_URLS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "holiday-money-updater"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:  # try the mirror
            print(f"  {url}: {e}")
            last = e
    raise RuntimeError(f"latest rates unavailable: {last}")


def next_month(ym):
    y, m = int(ym[:4]), int(ym[5:])
    return f"{y + 1}-01" if m == 12 else f"{y}-{m + 1:02d}"


def latest_only(latest):
    """Put today's rate into the current month, keeping the stored history."""
    with open(OUT) as f:
        data = json.load(f)
    day = latest.get("date", "")
    usd = latest.get("usd") or {}
    if len(day) != 10:
        sys.exit(f"Bad date in latest rates: {day!r}")
    age = (date.today() - date.fromisoformat(day)).days
    if age > 10:
        sys.exit(f"Latest rates look stale: {day} is {age} days old")
    if day <= data["asof"]:
        print(f"No newer rates (have {data['asof']}, source has {day}).")
        return
    ym, anchor = day[:7], data["anchor"]
    if ym < anchor:
        sys.exit(f"Latest month {ym} is older than stored month {anchor}")
    gap = 0
    while anchor < ym:  # count new months to add
        anchor = next_month(anchor)
        gap += 1
    series = data["series"]
    for cur, q in PAIRS.items():
        r = usd.get(cur.lower())
        if not isinstance(r, (int, float)) or r <= 0:
            sys.exit(f"{cur}: missing or bad latest rate {r!r}")
        val = round(r if q == "USDX" else 1 / r, 6)
        old = series[cur]["v"][0]
        if abs(val / old - 1) > MAX_JUMP:
            sys.exit(f"{cur}: latest {val} is too far from stored {old}; not updating")
        v = series[cur]["v"]
        if gap == 0:
            v[0] = val
        else:  # months with no stored close take the latest rate
            series[cur]["v"] = [val] * gap + v
    data.update({"asof": day, "anchor": ym, "latest_source": "currency-api",
                 "source": "Alpha Vantage FX_MONTHLY (history) + currency-api (latest)"})
    with open(OUT, "w") as f:
        json.dump(data, f, separators=(",", ":"))
        f.write("\n")
    print(f"Wrote {OUT}: latest rates as of {day}" + (f", {gap} new month(s)" if gap else ""))


def main():
    key = os.environ.get("ALPHAVANTAGE_API_KEY", "").strip()
    if "--latest-file" in sys.argv:
        with open(sys.argv[sys.argv.index("--latest-file") + 1]) as f:
            latest_only(json.load(f))
        return
    if not key:
        print("No ALPHAVANTAGE_API_KEY: updating the current month from currency-api.")
        latest_only(fetch_latest())
        return
    raw = {}
    for cur, q in PAIRS.items():
        print(f"Fetching {cur}…")
        raw[cur] = fetch(cur, q, key)
        time.sleep(15)  # stay well under the free tier's per-minute limit

    # Newest month that every currency has, and the latest trading day in it.
    anchor = min(max(r) for r in raw.values())
    asof = min(r[anchor][0] for r in raw.values())
    today = date.today()
    age = (today - date.fromisoformat(asof)).days
    if age > 45:
        sys.exit(f"Data looks stale: newest common date {asof} is {age} days old")

    series = {}
    for cur, q in PAIRS.items():
        rows, vals, ym = raw[cur], [], anchor
        months = sorted(rows, reverse=True)
        oldest = months[-1]
        while ym >= oldest:
            # A missing month takes the nearest older close, so months stay aligned.
            have = next(m for m in months if m <= ym)
            vals.append(round(rows[have][1], 6))
            ym = prev_month(ym)
        if len(vals) < MIN_MONTHS:
            sys.exit(f"{cur}: only {len(vals)} months of history")
        series[cur] = {"q": q, "v": vals}

    out = {"asof": asof, "anchor": anchor, "source": "Alpha Vantage FX_MONTHLY",
           "series": series}
    old = None
    if os.path.exists(OUT):
        with open(OUT) as f:
            old = json.load(f)
    if old and old.get("series") == series and old.get("asof") == asof:
        print("No change.")
        return
    with open(OUT, "w") as f:
        json.dump(out, f, separators=(",", ":"))
        f.write("\n")
    print(f"Wrote {OUT}: as of {asof}, {len(series)} currencies")


if __name__ == "__main__":
    main()
