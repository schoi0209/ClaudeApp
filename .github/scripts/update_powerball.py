# TEMPORARY diagnostic (branch powerball-debug only): dump what the parser sees.
import re, html, urllib.request
H={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36","Accept":"text/html,application/xhtml+xml","Accept-Language":"en-AU,en;q=0.9"}
def text(u):
    raw=urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=30).read().decode("utf-8","ignore")
    raw=re.sub(r"<script.*?</script>"," ",raw,flags=re.S|re.I); raw=re.sub(r"<style.*?</style>"," ",raw,flags=re.S|re.I)
    return raw, re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",raw)))
for name,u in [("powerball.net","https://www.powerball.net/australia/results"),("national-lottery","https://australia.national-lottery.com/powerball/results")]:
    raw,t=text(u)
    ms=list(re.finditer(r"Draw\s+\d{3,5}",t))
    print(f"##### {name}: {len(ms)} 'Draw N' markers")
    for m in ms[:6]: print("  [DRAW]", t[max(0,m.start()-70):m.end()+170])
    ds=list(re.finditer(r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\b",t))
    print(f"  {len(ds)} day-month dates; first 5 in context:")
    for m in ds[:5]: print("  [DATE]", t[max(0,m.start()-60):m.end()+150])
    i=raw.find("1591"); print("  [RAW around 1591]", re.sub(r"\s+"," ",raw[max(0,i-500):i+400]) if i>=0 else "1591 not in raw")
