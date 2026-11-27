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
    emails the repo owner, whenever: a site answers but can't be read (layout
    changed, or a block page / HTTP 4xx), trusted sources disagree, there is a
    gap or an implausible date, or the page is more than STALE_DAYS old with
    nothing newer anywhere.
  * Network trouble is retried (3 attempts per site, the later ones over IPv4).
    If no site can be reached at all, that run only warns and changes nothing:
    the next week's run backfills the missed draw. If it is still unreachable
    by then, the page has gone stale and the run fails as above.
  Exit code 0 means the page was updated, or there is legitimately nothing new.

Uses only the Python standard library.

Usage:
    python .github/scripts/update_powerball.py              # fetch live, patch
    python .github/scripts/update_powerball.py --dry-run    # fetch live, no write
    python .github/scripts/update_powerball.py --from-html a.html [b.html]   # test
"""
import argparse
import os
import datetime as dt
import html as _html
import http.client
import re
import socket
import sys
import time
import urllib.error
import urllib.request

HTML_FILE = "powerball-au.html"
# Other pages that embed the same DRAWS_RAW data and are kept in step with it.
ALSO_FILES = ["powerball-au-classic.html"]

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

# Per-draw prize pages, used to read how many Division 1 (7 + Powerball) entries won.
DIVIDEND_SOURCES = [
    ("powerball.net", "https://www.powerball.net/australia/results/{d:%Y-%m-%d}"),
    ("lotteryextreme", "https://www.lotteryextreme.com/australia/powerball-dividends({d:%Y-%m-%d})"),
]
WINNERS_WINDOW = 20      # only draws shown in the Recent Draws table
WINNERS_PER_RUN = 3      # at most this many draws are looked up per run
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

ATTEMPTS = 3
TIMEOUT = 45            # seconds per attempt
BACKOFF = (15, 30)      # seconds to wait before attempts 2 and 3


def fetch_once(url, ipv4_only=False):
    req = urllib.request.Request(url, headers=HEADERS)
    orig = socket.getaddrinfo
    if ipv4_only:   # some runners have IPv6 routes that hang; IPv4 sidesteps them
        socket.getaddrinfo = (lambda host, port, family=0, *a, **k:
                              orig(host, port, socket.AF_INET, *a, **k))
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.read().decode("utf-8", "ignore")
    finally:
        socket.getaddrinfo = orig


def fetch_source(name, url, attempts=ATTEMPTS):
    """
    Returns ('ok', (status, body)), ('broken', why) for an answer that won't fix
    itself (HTTP 4xx), or ('unreachable', why) after every attempt hit network
    trouble or HTTP 5xx.
    """
    why = ""
    for attempt in range(1, attempts + 1):
        if attempt > 1:
            time.sleep(BACKOFF[attempt - 2])
        ipv4 = attempt > 1
        try:
            status, body = fetch_once(url, ipv4_only=ipv4)
            if attempt > 1:
                log(f"{name}: succeeded on attempt {attempt} (IPv4)")
            return "ok", (status, body)
        except urllib.error.HTTPError as e:
            if not 500 <= e.code < 600:
                log(f"{name}: HTTP {e.code} (blocked or gone)")
                return "broken", f"HTTP {e.code}"
            why = f"HTTP {e.code}"
        except (OSError, http.client.HTTPException) as e:   # timeouts, resets, DNS, TLS
            why = f"{e.__class__.__name__}: {getattr(e, 'reason', e)}"
        log(f"{name}: attempt {attempt}/{attempts} failed ({why})")
    return "unreachable", why


DIV1_RE = re.compile(r"Div(?:ision)?\.?\s*1\b(.{0,200}?)Div(?:ision)?\.?\s*2\b", re.I | re.S)
MATCH_SPEC_RE = re.compile(r"(?:Match\s*)?\d\s*\+\s*(?:\d|PB|Powerball)\b|Match\s*\d\b", re.I)
AMOUNT_RE = re.compile(r"\$\s?(\d[\d,]*(?:\.\d+)?)")


def parse_div1_winners(text, jackpot):
    """
    Number of Division 1 winning entries from a prize-breakdown page, or None.

    Reads the stretch between "Division 1" and "Division 2", drops the match
    description ("Match 7+1", "7 + PB") and the dollar amounts, and looks at the
    whole numbers left. A count is only believed when it explains the jackpot:
    winners x prize per winner must come within 2% of the draw's jackpot.
    A lone 0 means nobody won.
    """
    m = DIV1_RE.search(text)
    if not m:
        return None
    seg = MATCH_SPEC_RE.sub(" ", m.group(1))
    prizes = [float(a.replace(",", "")) for a in AMOUNT_RE.findall(seg)]
    seg = AMOUNT_RE.sub(" ", seg)
    counts = [int(x.replace(",", "")) for x in re.findall(r"(?<![\d.])\d[\d,]*(?![\d.])", seg)]
    counts = [n for n in counts if 0 <= n <= 100]
    if counts == [0]:
        return 0
    if not jackpot:
        return None
    fits = {n for n in counts if n > 0 for p in prizes if p > 0 and abs(n * p - jackpot) <= 0.02 * jackpot}
    return fits.pop() if len(fits) == 1 else None


def to_text(raw):
    """Strip HTML to one collapsed line of visible text."""
    raw = re.sub(r"<script.*?</script>", " ", raw, flags=re.S | re.I)
    raw = re.sub(r"<style.*?</style>", " ", raw, flags=re.S | re.I)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = _html.unescape(raw)
    return re.sub(r"\s+", " ", raw)


MONTH_RE = (r"(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|"
            r"Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)")
DATE_RE = re.compile(r"\b(\d{1,2})\s+" + MONTH_RE + r"\b(?:\s+(20\d{2}))?", re.I)
MARK_RE = re.compile(r"\s*Draw\s+(\d{3,5})\b", re.I)
BEFORE_RE = re.compile(
    r"Draw\s+(\d{3,5})\s*[-–]?\s*(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*\s*,?\s*$", re.I)
TOKEN_RE = re.compile(r"\s*(\$?\d[\d,.]*|[^\s\d]+)")
# After the balls: optional "Draw N", optional winner count, optional "Jackpot:",
# then the dollar amount. powerball.net: "... 2 Draw 1591 1,123,930 $40,000,000";
# national-lottery's top draw: "... 16 Jackpot: $60,000,000".
JP_RE = re.compile(r"\s*(?:Draw\s+\d{3,5}\s+)?(?:\d[\d,]*\s+)?(?:Jackpot\s*:?\s*)?"
                   r"\$\s?(\d[\d,]*(?:\.\d+)?)", re.I)
JP_MIN, JP_MAX = 1_000_000, 2_000_000_000


def _read_run(text, pos):
    """Consecutive 1-2 digit numbers starting at pos; any other token ends it."""
    nums = []
    while len(nums) < 12:
        m = TOKEN_RE.match(text, pos)
        if not m or not (m.group(1).isdigit() and len(m.group(1)) <= 2):
            break
        nums.append(int(m.group(1)))
        pos = m.end()
    return nums, pos


def _guess_year(month, day, today):
    """For dates printed without a year: the year that puts it nearest today."""
    best = None
    for y in (today.year - 1, today.year, today.year + 1):
        try:
            d = dt.date(y, month, day)
        except ValueError:
            continue
        if best is None or abs((d - today).days) < abs((best - today).days):
            best = d
    return best


def parse_draws(text, today, jackpots=None):
    """
    Return {draw_no: (date, [7 sorted mains], pb)} found in page text.

    Anchored on dates, because on every layout seen so far the 8 numbers
    (7 main balls, then the Powerball) come right after a draw's date. The
    'Draw N' label may sit before the date, between the date and the balls,
    or just after the balls; all three are accepted:
        national-lottery: "Draw 1591 Thursday 12 November 2 7 11 13 25 27 31 2 View"
        powerball.net top: "Thursday, 19 November 2026 Draw 1592 3 4 9 16 21 32 35 16"
        powerball.net list: "Thursday, 12 November 2026 2 7 11 13 25 27 31 2 Draw 1591"
    Exactly 8 numbers are required; anything else after the date is ignored.
    A date printed without a year gets the year that puts it nearest today.
    If a jackpots dict is passed, {draw_no: dollars} is filled in for draws whose
    jackpot is printed right after the balls.
    """
    text = re.sub(r"[·•|]", " ", text)   # middots, bullets, bars as separators
    draws = {}
    for dm in DATE_RE.finditer(text):
        month = MONTHS[dm.group(2)[:3].lower()]
        day = int(dm.group(1))
        pos, draw_no = dm.end(), None

        between = MARK_RE.match(text, pos)
        if between:
            draw_no, pos = int(between.group(1)), between.end()
        nums, end = _read_run(text, pos)
        if len(nums) != N_MAIN + 1:
            continue
        if draw_no is None:
            before = BEFORE_RE.search(text[max(0, dm.start() - 40):dm.start()])
            if before:
                draw_no = int(before.group(1))
        if draw_no is None:
            after = MARK_RE.match(text, end)
            if after:
                draw_no = int(after.group(1))
        if draw_no is None:
            continue

        if dm.group(3):
            try:
                date = dt.date(int(dm.group(3)), month, day)
            except ValueError:
                continue
        else:
            date = _guess_year(month, day, today)
            if date is None:
                continue

        mains, pb = nums[:N_MAIN], nums[N_MAIN]
        if any(not (MAIN_MIN <= x <= MAIN_MAX) for x in mains):
            continue
        if len(set(mains)) != N_MAIN or not (PB_MIN <= pb <= PB_MAX):
            continue
        draws.setdefault(draw_no, (date, sorted(mains), pb))
        if jackpots is not None:
            jm = JP_RE.match(text, end)
            if jm:
                amount = int(float(jm.group(1).replace(",", "")))
                if JP_MIN <= amount <= JP_MAX:
                    jackpots.setdefault(draw_no, amount)
    return draws


# ── the page ───────────────────────────────────────────────────────────

ROW_RE = re.compile(
    r'\{draw:(\d+),date:"(\d{1,2}) ([A-Za-z]{3,9}) (\d{4})",nums:\[([\d,]+)\],pb:(\d+)'
    r'(?:,jp:(\d+))?(?:,w:(\d+))?\}')


def page_draws(page):
    out = {}
    for dn, d, mon, y, nums, pb, _jp, _w in ROW_RE.findall(page):
        out[int(dn)] = (dt.date(int(y), MONTHS[mon[:3].lower()], int(d)),
                        sorted(int(x) for x in nums.split(",")), int(pb))
    if not out:
        fail("could not read any existing draws from the page")
    return out


def page_jackpots(page):
    return {int(m[0]): int(m[6]) for m in ROW_RE.findall(page) if m[6]}


def page_winners(page):
    return {int(m[0]): int(m[7]) for m in ROW_RE.findall(page) if m[7]}


def build_rows(new, jps, wins):
    lines = []
    for dn in sorted(new, reverse=True):
        date, mains, pb = new[dn]
        jp = f",jp:{jps[dn]}" if dn in jps else ""
        jp += f",w:{wins[dn]}" if dn in wins else ""
        lines.append(
            f'  {{draw:{dn},date:"{date.day:02d} {MON_ABBR[date.month]} {date.year}",'
            f'nums:[{",".join(map(str, mains))}],pb:{pb}{jp}}},')
    return "\n".join(lines)


def patch(page, new, jps, wins):
    latest = max(new)
    date, mains, pb = new[latest]
    d = f"{date.day:02d} {MON_ABBR[date.month]} {date.year}"
    nums = ", ".join(map(str, mains))
    subs = [
        (r"(const DRAWS_RAW=\[\n)", lambda mm: mm.group(1) + build_rows(new, jps, wins) + "\n"),
        (r"DRAW #\d+ · \d{2} [A-Z]{3} 20\d{2}",
         f"DRAW #{latest} · {d.upper()}"),
        (r"Latest: [\d, ]+ \+ PB \d+", f"Latest: {nums} + PB {pb}"),
        (r"Draw #\d+ · [A-Za-z]{3} \d{2} [A-Za-z]{3} 20\d{2}</strong> · [\d, ]+ \+ Powerball \d+",
         f"Draw #{latest} · {WEEKDAY[date.weekday()]} {d}</strong> · {nums} + Powerball {pb}"),
        (r"through Draw #\d+", f"through Draw #{latest}"),
    ]
    # The data array is required. The text spots only exist on the classic
    # layout (the current page works them out from the data), so they're
    # updated where present.
    for i, (pattern, repl) in enumerate(subs):
        page, n = re.subn(pattern, repl, page, count=1)
        if n != 1 and i == 0:
            fail(f"page layout changed; could not find the spot for: {pattern[:45]}")
    # Cosmetic: stretch the "2024–2026 · Latest:" range when a new year starts.
    page = re.sub(r"(\d{4})–(\d{4})( · Latest:)",
                  lambda m: f"{m.group(1)}–{max(int(m.group(2)), date.year)}{m.group(3)}",
                  page, count=1)
    return page


def fill_jackpots(page, fill):
    """Add jp to existing rows that don't have one yet."""
    for dn, jp in fill.items():
        page, n = re.subn(r'(\{draw:%d,date:"[^"]+",nums:\[[\d,]+\],pb:\d+)((?:,w:\d+)?)\}' % dn,
                          lambda m: f"{m.group(1)},jp:{jp}{m.group(2)}}}", page, count=1)
        if n != 1:
            fail(f"could not find row #{dn} to add its jackpot")
    return page


def fill_winners(page, fill):
    """Add w (Division 1 winning entries) to existing rows that don't have one yet."""
    for dn, w in fill.items():
        page, n = re.subn(r'(\{draw:%d,date:"[^"]+",nums:\[[\d,]+\],pb:\d+(?:,jp:\d+)?)\}' % dn,
                          lambda m: f"{m.group(1)},w:{w}}}", page, count=1)
        if n != 1:
            fail(f"could not find row #{dn} to add its winners")
    return page


def lookup_winners(cands, div_html):
    """
    {draw_no: Division 1 winners} for cands = {draw_no: (date, jackpot, next_jackpot)}.
    Each draw's prize pages are read (one attempt each). Sources that can be read
    must agree, and the count must fit the jackpot rolling over or resetting.
    """
    out = {}
    for dn in sorted(cands, reverse=True):
        date, jp, next_jp = cands[dn]
        found = []
        if div_html is not None:
            for path in div_html.get(dn, []):
                with open(path, encoding="utf-8") as f:
                    found.append((path, parse_div1_winners(to_text(f.read()), jp)))
        else:
            for name, pattern in DIVIDEND_SOURCES:
                kind, info = fetch_source(f"{name} #{dn} prizes", pattern.format(d=date), attempts=1)
                if kind == "ok":
                    found.append((name, parse_div1_winners(to_text(info[1]), jp)))
        got = {n for _, n in found if n is not None}
        detail = ", ".join(f"{name} {'?' if n is None else n}" for name, n in found) or "no page read"
        if len(got) != 1:
            log(f"#{dn} Division 1 winners: unknown ({detail})")
            continue
        n = got.pop()
        if next_jp is not None and ((n > 0 and next_jp > jp) or (n == 0 and next_jp < jp)):
            warn(f"#{dn}: {n} Division 1 winners doesn't fit the next jackpot "
                 f"({money(jp)} then {money(next_jp)}); not recorded")
            continue
        log(f"#{dn} Division 1 winners: {n} ({detail})")
        out[dn] = n
    return out


def update_files(paths, primary_page, cur_max, new, jp_all, wins):
    """{path: new text} for every page that changes. Pages not at cur_max are skipped."""
    out = {}
    for i, path in enumerate(paths):
        if i == 0:
            text = primary_page
        else:
            with open(path, encoding="utf-8") as f:
                text = f.read()
        rows = page_draws(text)
        if max(rows) != cur_max:
            warn(f"{path} ends at #{max(rows)}, not #{cur_max}; left unchanged")
            continue
        have = page_jackpots(text)
        fill = {dn: a for dn, a in jp_all.items() if dn in rows and dn not in have}
        result = patch(text, new, jp_all, wins) if new else text
        have_w = page_winners(text)
        fill_w = {dn: w for dn, w in wins.items() if dn in rows and dn not in have_w}
        if fill_w:
            result = fill_winners(result, fill_w)
        if fill:
            log(f"{path}: adding missing jackpots "
                + ", ".join(f"#{dn} {money(a)}" for dn, a in sorted(fill.items())))
            result = fill_jackpots(result, fill)
        if result != text:
            out[path] = result
    return out


def money(n):
    return f"${n / 1e6:.1f}M".replace(".0M", "M")


# ── main ───────────────────────────────────────────────────────────────

def show(v):
    date, mains, pb = v
    return f"{date:%d %b %Y} {mains} + PB{pb}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=HTML_FILE)
    ap.add_argument("--also", nargs="*", default=ALSO_FILES,
                    help="other pages with the same data to update (skipped if missing)")
    ap.add_argument("--from-html", nargs="+", help="parse local files instead of fetching")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--stale-days", type=int, default=STALE_DAYS,
                    help="fail if the page is older than this with nothing new (default %(default)s)")
    ap.add_argument("--today", help="YYYY-MM-DD, for testing")
    ap.add_argument("--div-html", nargs="*", default=[],
                    help="DRAW=FILE prize pages to read instead of fetching (testing)")
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
                jps = {}
                per_source.append((path, parse_draws(to_text(f.read()), today, jps), jps))
    unreachable = []
    if not args.from_html:
        for name, url in SOURCES:
            kind, info = fetch_source(name, url)
            parsed, jps = {}, {}
            if kind == "ok":
                status, body = info
                parsed = parse_draws(to_text(body), today, jps)
                log(f"{name}: HTTP {status}, {len(body):,} chars, {len(parsed)} draws parsed, "
                    f"{len(jps)} jackpots")
            elif kind == "unreachable":
                unreachable.append(name)
            per_source.append((name, parsed, jps))

    if not any(p for _, p, _j in per_source):
        if per_source and len(unreachable) == len(per_source):
            age = (today - cur_date).days
            if age > args.stale_days:
                fail(f"no source could be reached, and the page latest #{cur_max} is {age} days old")
            warn("no source could be reached this run (network trouble); nothing changed, "
                 "and next week's run will catch up")
            return
        fail("no source returned any readable draws; the sites may have changed or be blocking")

    # 2) Trust a source only if it reproduces draws the page already has.
    trusted = []
    for name, parsed, jps in per_source:
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
        trusted.append((name, parsed, jps))

    if not trusted:
        fail("no source could be verified against the page, so nothing was written")

    # 3) Merge new draws; trusted sources that both show a draw must agree.
    new, confirmed_by = {}, {}
    for name, parsed, _jps in trusted:
        for dn, v in parsed.items():
            if dn <= cur_max:
                continue
            if dn in new and new[dn] != v:
                fail(f"sources disagree on #{dn}: {show(new[dn])} vs {name} {show(v)}")
            new.setdefault(dn, v)
            confirmed_by.setdefault(dn, []).append(name)

    # Jackpots from trusted sources (first one wins; a mismatch is only a warning).
    jp_all = {}
    for name, _parsed, jps in trusted:
        for dn, amount in jps.items():
            if dn in jp_all and jp_all[dn] != amount:
                warn(f"{name}: jackpot for #{dn} is {money(amount)}, another source says "
                     f"{money(jp_all[dn])}; keeping the first")
            jp_all.setdefault(dn, amount)
    paths = [args.file] + [p for p in args.also if p != args.file and os.path.exists(p)]

    # Division 1 winners for recent draws that don't have them yet.
    all_dates = {dn: v[0] for dn, v in {**known, **new}.items()}
    all_jp = {**page_jackpots(page), **jp_all}
    have_w = page_winners(page)
    recent = sorted(all_dates, reverse=True)[:WINNERS_WINDOW]
    want = [dn for dn in recent if dn not in have_w and dn in all_jp][:WINNERS_PER_RUN]
    div_html = None
    if args.from_html:
        div_html = {}
        for spec in args.div_html:
            dn, path = spec.split("=", 1)
            div_html.setdefault(int(dn), []).append(path)
    wins = {}
    if want and (div_html is None or div_html):
        wins = lookup_winners({dn: (all_dates[dn], all_jp[dn], all_jp.get(dn + 1)) for dn in want}, div_html)

    if not new:
        age = (today - cur_date).days
        if age > args.stale_days:
            fail(f"page latest #{cur_max} is {age} days old and no source has anything newer")
        changes = update_files(paths, page, cur_max, {}, jp_all, wins)
        if not changes:
            log("nothing new yet; page unchanged.")
            return
        write_changes(changes, args.dry_run)
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
        jp = f" | jackpot {money(jp_all[dn])}" if dn in jp_all else " | jackpot unknown"
        log(f"new #{dn} {show(new[dn])}{jp}  [{', '.join(confirmed_by[dn])}]")

    write_changes(update_files(paths, page, cur_max, new, jp_all, wins), args.dry_run)
    log(f"now through #{max(new)} ({len(new)} new).")


def write_changes(changes, dry_run):
    if dry_run:
        log("dry run: not writing " + ", ".join(changes))
        return
    for path, text in changes.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        log(f"updated {path}")


if __name__ == "__main__":
    main()
