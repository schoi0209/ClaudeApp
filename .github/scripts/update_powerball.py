#!/usr/bin/env python3
"""
Weekly auto-updater for powerball-au.html (SunnyApps).

Run by .github/workflows/update-powerball.yml every Thursday after the draw.
Fetches the latest Australian Powerball results, checks them hard, and patches
powerball-au.html: the draw data plus the header badge, the data-info line,
the footer line and the insight reference.

How it stays honest:
  * A source is only trusted if the draws it shows that are already on the page
    match the page exactly (numbers, Powerball and date). A source whose layout
    changed, or that serves a block page, is ignored instead of believed.
  * When two trusted sources both show a new draw, they must agree.
  * New draws must continue the page without gaps, one week apart, and not be
    dated in the future.
  * It never fails silently. Exit code 1 turns the Actions run red, so GitHub
    emails the repo owner, whenever: no source can be read, trusted sources
    disagree, there is a gap or an implausible date, or the page is more than
    STALE_DAYS old with nothing newer anywhere.
  Exit code 0 means the page was updated, or there is legitimately nothing new.

Uses only the Python standard library.

Usage:
    python .github/scripts/update_powerball.py              # fetch live, patch
    python .github/scripts/update_powerball.py --dry-run    # fetch live, no write
    python .github/scripts/update_powerball.py --from-html a.html [b.html]   # test
"""
import argparse
import datetime as dt
import html as _html
import re
import sys
import urllib.error
import urllib.request

HTML_FILE = "powerball-au.html"

SOURCES = [
    ("powerball.net", "https://www.powerball.net/australia/results"),
    ("national-lottery", "https://australia.national-lottery.com/powerball/results"),
]

# A normal browser identity. No Accept-Encoding header on purpose: the server
# then answers with plain text. Advertising brotli ("br") without a decoder
# installed leaves the page as unreadable bytes.
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-AU,en;q=0.9",
}

STALE_DAYS = 8          # draws are weekly; older than this with nothing new = broken
MAIN_MIN, MAIN_MAX, N_MAIN = 1, 35, 7
PB_MIN, PB_MAX = 1, 20

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun",
     "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
MON_ABBR = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
WEEKDAY = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def log(msg):
    print(f"[powerball] {msg}", flush=True)


def fail(msg):
    print(f"::error::{msg}", flush=True)
    log(f"ERROR: {msg}")
    sys.exit(1)


def warn(msg):
    print(f"::warning::{msg}", flush=True)
    log(f"WARNING: {msg}")


# ── fetching and parsing ───────────────────────────────────────────────

def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.read().decode("utf-8", "ignore")


def to_text(raw):
    """Strip HTML to one collapsed line of visible text."""
    raw = re.sub(r"<script.*?</script>", " ", raw, flags=re.S | re.I)
    raw = re.sub(r"<style.*?</style>", " ", raw, flags=re.S | re.I)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = _html.unescape(raw)
    return re.sub(r"\s+", " ", raw)


def parse_draws(text):
    """
    Return {draw_no: (date, [7 sorted mains], pb)} found in page text.

    Markup independent: find each 'Draw <N>', take the date next to it (before
    it on powerball.net, after it on national-lottery), then read the run of
    1-2 digit numbers that follows: 7 main balls, then the Powerball. Winner
    counts and prize amounts end the run. Rows without a 4-digit year are
    skipped; the newest draws always carry one.
    """
    draws = {}
    date_re = re.compile(r"(\d{1,2})\s+([A-Za-z]{3,9})\s+(20\d{2})")
    for m in re.finditer(r"Draw\s+(\d{3,5})", text):
        draw_no = int(m.group(1))
        head = text[max(0, m.start() - 48):m.start()]
        after = text[m.end():m.end() + 180]

        dm = None
        for cand in date_re.finditer(head):
            dm = cand                       # the last date before the marker
        date_in_after = dm is None
        if date_in_after:
            dm = date_re.search(after)
        if dm is None:
            continue
        mon = MONTHS.get(dm.group(2)[:3].lower())
        if not mon:
            continue
        try:
            date = dt.date(int(dm.group(3)), mon, int(dm.group(1)))
        except ValueError:
            continue

        # If the date sat after the marker, start past it so the day of the
        # month isn't read as a ball.
        region = after[dm.end():] if date_in_after else after
        nums = []
        for tok in re.finditer(r"\d{1,3}", region):
            v = int(tok.group())
            if v > 99:
                break
            nums.append(v)
            if len(nums) >= 12:
                break
        if len(nums) < N_MAIN + 1:
            continue
        mains, pb = nums[:N_MAIN], nums[N_MAIN]
        if any(not (MAIN_MIN <= x <= MAIN_MAX) for x in mains):
            continue
        if len(set(mains)) != N_MAIN or not (PB_MIN <= pb <= PB_MAX):
            continue
        draws.setdefault(draw_no, (date, sorted(mains), pb))
    return draws


# ── the page ───────────────────────────────────────────────────────────

ROW_RE = re.compile(
    r'\{draw:(\d+),date:"(\d{1,2}) ([A-Za-z]{3,9}) (\d{4})",nums:\[([\d,]+)\],pb:(\d+)\}')


def page_draws(page):
    out = {}
    for dn, d, mon, y, nums, pb in ROW_RE.findall(page):
        out[int(dn)] = (dt.date(int(y), MONTHS[mon[:3].lower()], int(d)),
                        sorted(int(x) for x in nums.split(",")), int(pb))
    if not out:
        fail("could not read any existing draws from the page")
    return out


def build_rows(new):
    lines = []
    for dn in sorted(new, reverse=True):
        date, mains, pb = new[dn]
        lines.append(
            f'  {{draw:{dn},date:"{date.day:02d} {MON_ABBR[date.month]} {date.year}",'
            f'nums:[{",".join(map(str, mains))}],pb:{pb}}},')
    return "\n".join(lines)


def patch(page, new):
    latest = max(new)
    date, mains, pb = new[latest]
    d = f"{date.day:02d} {MON_ABBR[date.month]} {date.year}"
    nums = ", ".join(map(str, mains))
    subs = [
        (r"(const DRAWS_RAW=\[\n)", lambda mm: mm.group(1) + build_rows(new) + "\n"),
        (r"DRAW #\d+ · \d{2} [A-Z]{3} 20\d{2}",
         f"DRAW #{latest} · {d.upper()}"),
        (r"Latest: [\d, ]+ \+ PB \d+", f"Latest: {nums} + PB {pb}"),
        (r"Draw #\d+ · [A-Za-z]{3} \d{2} [A-Za-z]{3} 20\d{2}</strong> · [\d, ]+ \+ Powerball \d+",
         f"Draw #{latest} · {WEEKDAY[date.weekday()]} {d}</strong> · {nums} + Powerball {pb}"),
        (r"through Draw #\d+", f"through Draw #{latest}"),
    ]
    for pattern, repl in subs:
        page, n = re.subn(pattern, repl, page, count=1)
        if n != 1:
            fail(f"page layout changed; could not find the spot for: {pattern[:45]}")
    return page


# ── main ───────────────────────────────────────────────────────────────

def show(v):
    date, mains, pb = v
    return f"{date:%d %b %Y} {mains} + PB{pb}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=HTML_FILE)
    ap.add_argument("--from-html", nargs="+", help="parse local files instead of fetching")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--today", help="YYYY-MM-DD, for testing")
    args = ap.parse_args()

    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    with open(args.file, encoding="utf-8") as f:
        page = f.read()
    known = page_draws(page)
    cur_max = max(known)
    cur_date = known[cur_max][0]
    log(f"page latest: #{cur_max} ({cur_date:%d %b %Y}); today {today}")

    # 1) Read every source and log exactly what happened.
    per_source = []
    if args.from_html:
        for path in args.from_html:
            with open(path, encoding="utf-8") as f:
                per_source.append((path, parse_draws(to_text(f.read()))))
    else:
        for name, url in SOURCES:
            try:
                status, body = fetch(url)
                parsed = parse_draws(to_text(body))
                log(f"{name}: HTTP {status}, {len(body):,} chars, {len(parsed)} draws parsed")
            except urllib.error.HTTPError as e:
                log(f"{name}: HTTP {e.code} (blocked or unavailable)")
                parsed = {}
            except Exception as e:  # network errors, timeouts
                log(f"{name}: failed to fetch ({e.__class__.__name__}: {e})")
                parsed = {}
            per_source.append((name, parsed))

    if not any(p for _, p in per_source):
        fail("no source returned any readable draws; the sites may have changed or be blocking")

    # 2) Trust a source only if it reproduces draws the page already has.
    trusted = []
    for name, parsed in per_source:
        parsed = {dn: v for dn, v in parsed.items() if v[0] <= today + dt.timedelta(days=1)}
        if not parsed:
            continue
        overlap = [dn for dn in parsed if dn in known]
        if not overlap:
            warn(f"{name}: shows nothing that is already on the page, so it cannot be checked; ignored")
            continue
        bad = [dn for dn in overlap if parsed[dn] != known[dn]]
        if bad:
            dn = bad[0]
            warn(f"{name}: disagrees with the page on #{dn} "
                 f"({show(parsed[dn])} vs page {show(known[dn])}); ignored")
            continue
        log(f"{name}: trusted (matches the page on {len(overlap)} known draws, "
            f"latest it shows #{max(parsed)})")
        trusted.append((name, parsed))

    if not trusted:
        fail("no source could be verified against the page, so nothing was written")

    # 3) Merge new draws; trusted sources that both show a draw must agree.
    new, confirmed_by = {}, {}
    for name, parsed in trusted:
        for dn, v in parsed.items():
            if dn <= cur_max:
                continue
            if dn in new and new[dn] != v:
                fail(f"sources disagree on #{dn}: {show(new[dn])} vs {name} {show(v)}")
            new.setdefault(dn, v)
            confirmed_by.setdefault(dn, []).append(name)

    if not new:
        age = (today - cur_date).days
        if age > STALE_DAYS:
            fail(f"page latest #{cur_max} is {age} days old and no source has anything newer")
        log("nothing new yet; page unchanged.")
        return

    # 4) Continuity: no gaps, exactly one week apart.
    missing = [dn for dn in range(cur_max + 1, max(new) + 1) if dn not in new]
    if missing:
        fail(f"missing draws {missing} between #{cur_max} and #{max(new)}; not writing a gap")
    prev = cur_date
    for dn in sorted(new):
        if (new[dn][0] - prev).days != 7:
            fail(f"#{dn} is dated {new[dn][0]:%d %b %Y}, expected {prev + dt.timedelta(days=7):%d %b %Y}")
        prev = new[dn][0]

    for dn in sorted(new):
        log(f"new #{dn} {show(new[dn])}  [{', '.join(confirmed_by[dn])}]")

    patched = patch(page, new)
    if args.dry_run:
        log("dry run: not writing.")
        return
    with open(args.file, "w", encoding="utf-8") as f:
        f.write(patched)
    log(f"updated {args.file}: now through #{max(new)} ({len(new)} new).")


if __name__ == "__main__":
    main()
