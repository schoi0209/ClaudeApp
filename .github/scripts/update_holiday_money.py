#!/usr/bin/env python3
"""Refresh holiday-money-data.json with monthly FX closes from Alpha Vantage.

Each series is stored newest month first. q="USDX" means units of X per 1 USD,
q="XUSD" means USD per 1 X. The file is only rewritten when every currency
downloads and passes validation, so a bad run never replaces good data.

Needs the ALPHAVANTAGE_API_KEY environment variable (a repo secret).
The free key allows about 25 calls a day; one run uses 15.
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


def main():
    key = os.environ.get("ALPHAVANTAGE_API_KEY", "").strip()
    if not key:
        sys.exit("ALPHAVANTAGE_API_KEY is not set")
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
