#!/usr/bin/env python3
"""
Australian Powerball Auto-Updater
Fetches latest draw results and patches powerball-au.html.
Runs weekly via GitHub Actions (Thursdays after draw).

Sources tried in order:
  1. australia.national-lottery.com (archive page)
  2. powerball.net JSON/HTML
  3. lotto.net
  4. ozlotteries.com
"""

import re, sys, time, json
from datetime import datetime
import requests
from bs4 import BeautifulSoup

HTML_FILE = "powerball-au.html"

MONTH_MAP = {
    "jan":"01","feb":"02","mar":"03","apr":"04","may":"05","jun":"06",
    "jul":"07","aug":"08","sep":"09","oct":"10","nov":"11","dec":"12",
    "january":"01","february":"02","march":"03","april":"04","june":"06",
    "july":"07","august":"08","september":"09","october":"10",
    "november":"11","december":"12"
}

MONTH_ABB = {
    "01":"Jan","02":"Feb","03":"Mar","04":"Apr","05":"May","06":"Jun",
    "07":"Jul","08":"Aug","09":"Sep","10":"Oct","11":"Nov","12":"Dec"
}

def std_date(day, month_word, year):
    """Return 'DD Mon YYYY' string."""
    m = MONTH_MAP.get(month_word.lower(), "01")
    return f"{int(day):02d} {MONTH_ABB[m]} {year}"

def get_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-AU,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    })
    return s

def parse_number_sequence(text, min_main=7, main_max=35, pb_max=20):
    """
    From a text blob, extract the most likely (7 main + 1 PB) combination.
    Returns (sorted_main_list, pb) or None.
    """
    nums = [int(n) for n in re.findall(r'\b(\d{1,2})\b', text)
            if 1 <= int(n) <= 35]
    if len(nums) < 8:
        return None
    # Last number <= 20 is likely PB
    for i in range(len(nums)-1, -1, -1):
        if nums[i] <= pb_max:
            pb = nums[i]
            main = sorted(set(nums[:i]))
            if len(main) == 7:
                return main, pb
    return None

# ── SOURCE 1: national-lottery.com ──────────────────────────
def source_national_lottery():
    draws = []
    year = datetime.now().year
    s = get_session()
    for y in [year, year-1]:
        url = f"https://australia.national-lottery.com/powerball/results-archive-{y}"
        try:
            r = s.get(url, timeout=15)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "lxml")
            # Each row: draw number, date, winning numbers
            rows = soup.select("table tr, .result-row, [class*='result']")
            for row in rows:
                txt = row.get_text(" ")
                draw_m = re.search(r'Draw\s+(\d{4})', txt)
                date_m = re.search(
                    r'(\d{1,2})\s+(January|February|March|April|May|June|July|'
                    r'August|September|October|November|December)\s+(\d{4})', txt, re.I)
                if draw_m and date_m:
                    parsed = parse_number_sequence(txt[date_m.end():date_m.end()+100])
                    if parsed:
                        main, pb = parsed
                        draws.append({
                            "draw": int(draw_m.group(1)),
                            "date_str": std_date(*date_m.groups()),
                            "nums": main, "pb": pb
                        })
        except Exception as e:
            print(f"  national-lottery {y}: {e}")
        time.sleep(0.5)
    return draws

# ── SOURCE 2: powerball.net/australia ───────────────────────
def source_powerball_net():
    draws = []
    s = get_session()
    # Try the archive pages
    year = datetime.now().year
    for y in [year, year-1]:
        url = f"https://www.powerball.net/australia/archive/{y}"
        try:
            r = s.get(url, timeout=15)
            if r.status_code != 200:
                url2 = "https://www.powerball.net/australia/results"
                r = s.get(url2, timeout=15)
                if r.status_code != 200:
                    continue
            soup = BeautifulSoup(r.text, "lxml")
            text = soup.get_text(" ")
            # Pattern from powerball.net: "Thursday, 9 April 2026 Draw 1560 3 15 17..."
            block_re = re.compile(
                r'(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,?\s+'
                r'(\d{1,2})\s+'
                r'(January|February|March|April|May|June|July|'
                r'August|September|October|November|December)\s+'
                r'(\d{4})\s+'
                r'(?:·?\s*)?Draw\s+(\d{4})'
                r'((?:\s*·?\s*\d{1,2}){8})', re.I
            )
            for m in block_re.finditer(text):
                day, mon, yr, draw_num, num_block = m.groups()
                parsed = parse_number_sequence(num_block)
                if parsed:
                    main, pb = parsed
                    draws.append({
                        "draw": int(draw_num),
                        "date_str": std_date(day, mon, yr),
                        "nums": main, "pb": pb
                    })
        except Exception as e:
            print(f"  powerball.net {y}: {e}")
        time.sleep(0.5)
    return draws

# ── SOURCE 3: lottolyzer.com ─────────────────────────────────
def source_lottolyzer():
    draws = []
    s = get_session()
    url = "https://lottolyzer.com/app/australia/powerball/results-page"
    try:
        r = s.get(url, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "lxml")
            text = soup.get_text(" ")
            draw_re = re.compile(
                r'(\d{4})\s+'
                r'(\d{1,2})\s+'
                r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+'
                r'(\d{4})\s+'
                r'((?:\d{1,2}\s+){7})'
                r'(\d{1,2})', re.I
            )
            for m in draw_re.finditer(text):
                draw_num, day, mon, yr, main_str, pb_str = m.groups()
                main = sorted(int(n) for n in main_str.split())
                pb = int(pb_str)
                if len(main) == 7 and 1 <= pb <= 20:
                    draws.append({
                        "draw": int(draw_num),
                        "date_str": std_date(day, mon, yr),
                        "nums": main, "pb": pb
                    })
    except Exception as e:
        print(f"  lottolyzer: {e}")
    return draws

# ── SOURCE 4: Wikipedia (most reliable, rarely blocked) ──────
def source_wikipedia():
    draws = []
    s = get_session()
    # Wikipedia API for Powerball (Australia) article
    url = (
        "https://en.wikipedia.org/w/api.php"
        "?action=parse&page=Powerball_(Australia)&prop=wikitext&format=json"
    )
    try:
        r = s.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
            # Look for recent draw tables
            draw_re = re.compile(
                r'\|\|\s*(\d{4})\s*\|\|\s*'  # draw number
                r'(\d{1,2})\s+(January|February|March|April|May|June|July|'
                r'August|September|October|November|December)\s+(\d{4})\s*\|\|\s*'
                r'((?:\d{1,2}[,\s]+){6}\d{1,2})\s*\|\|\s*(\d{1,2})', re.I
            )
            for m in draw_re.finditer(wikitext):
                draw_num, day, mon, yr, main_str, pb_str = m.groups()
                main = sorted(int(n) for n in re.findall(r'\d+', main_str))
                pb = int(pb_str)
                if len(main) == 7 and 1 <= pb <= 20:
                    draws.append({
                        "draw": int(draw_num),
                        "date_str": std_date(day, mon, yr),
                        "nums": main, "pb": pb
                    })
    except Exception as e:
        print(f"  wikipedia: {e}")
    return draws

# ── MERGE & DEDUPLICATE ──────────────────────────────────────
def collect_all_draws():
    all_draws = []
    sources = [
        ("national-lottery.com", source_national_lottery),
        ("powerball.net",        source_powerball_net),
        ("lottolyzer.com",       source_lottolyzer),
        ("wikipedia.org",        source_wikipedia),
    ]
    for name, fn in sources:
        print(f"  → {name}...", end=" ", flush=True)
        try:
            found = fn()
            print(f"{len(found)} draws")
            all_draws.extend(found)
        except Exception as e:
            print(f"failed ({e})")

    # Deduplicate — keep first occurrence (prefer earlier sources)
    seen = {}
    for d in all_draws:
        if d["draw"] not in seen:
            seen[d["draw"]] = d
    return sorted(seen.values(), key=lambda x: x["draw"], reverse=True)

# ── HTML PATCH ───────────────────────────────────────────────
def get_current_draws(html):
    pat = re.compile(r'\{draw:(\d+),date:"([^"]+)",nums:\[([^\]]+)\],pb:(\d+)\}')
    draws = []
    for m in pat.finditer(html):
        nums = [int(n.strip()) for n in m.group(3).split(",")]
        draws.append({
            "draw": int(m.group(1)),
            "date_str": m.group(2),
            "nums": nums,
            "pb": int(m.group(4))
        })
    return draws

def fmt(d):
    nums = ",".join(str(n) for n in sorted(d["nums"]))
    return f'  {{draw:{d["draw"]},date:"{d["date_str"]}",nums:[{nums}],pb:{d["pb"]}}},'

def patch_html(html, new_draws):
    existing = get_current_draws(html)
    have = {d["draw"] for d in existing}
    to_add = sorted(
        [d for d in new_draws if d["draw"] not in have],
        key=lambda x: x["draw"], reverse=True
    )
    if not to_add:
        return html, False

    print(f"  ✚ Inserting draws: {[d['draw'] for d in to_add]}")

    # Insert before first existing draw line
    first = re.search(r'(\s*\{draw:\d+,date:"[^"]+",nums:\[[^\]]+\],pb:\d+\},)', html)
    if not first:
        print("  ✗ Insertion point not found!")
        return html, False

    insert_text = "\n".join(fmt(d) for d in to_add) + "\n"
    html = html[:first.start()] + "\n" + insert_text + html[first.start():]

    top = to_add[0]
    nums_str  = ", ".join(str(n) for n in top["nums"])
    date_str  = top["date_str"]
    draw_num  = top["draw"]
    pb_str    = str(top["pb"])

    # Badge: "DRAW #1560 · 9 APR 2026"
    html = re.sub(
        r'DRAW #\d+\s*·\s*[\d\w ]+\d{4}',
        f'DRAW #{draw_num} · {date_str.upper()}',
        html
    )
    # data-info latest line
    html = re.sub(
        r'Latest:[\d,\s]+ \+ PB \d+',
        f'Latest: {nums_str} + PB {pb_str}',
        html
    )
    # Footer
    html = re.sub(
        r'Draw #\d+ · Thu [\d\w ]+ \d{4}</strong> · [\d,\s]+ \+ Powerball \d+',
        f'Draw #{draw_num} · Thu {date_str}</strong> · {nums_str} + Powerball {pb_str}',
        html
    )
    return html, True

# ── MAIN ─────────────────────────────────────────────────────
def main():
    now = datetime.now()
    print(f"\n{'='*56}")
    print(f"  🎱 Powerball Auto-Updater — {now.strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*56}\n")

    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    current = get_current_draws(html)
    top_cur = current[0]["draw"] if current else 0
    print(f"  Current top draw in file : #{top_cur}")

    print("\n📡 Scraping sources...")
    draws = collect_all_draws()

    if not draws:
        print("\n❌ No draws retrieved from any source. Exiting.")
        sys.exit(0)

    top_new = draws[0]["draw"]
    print(f"\n  Latest available draw    : #{top_new}")

    if top_new <= top_cur:
        print(f"  ✅ Already up-to-date (Draw #{top_cur}). Nothing to do.")
        sys.exit(0)

    print(f"\n✏️  Patching HTML...")
    updated, changed = patch_html(html, draws)

    if not changed:
        print("  No changes were made.")
        sys.exit(0)

    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(updated)

    top = draws[0]
    print(f"\n✅ Done! New top draw: #{top['draw']} · {top['date_str']}")
    print(f"   Numbers : {top['nums']} + PB {top['pb']}\n")

if __name__ == "__main__":
    main()
