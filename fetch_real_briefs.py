#!/usr/bin/env python3
"""Skuplja PRAVE odgovore modela preko Overnight UI-ja (port 8000, nginx proxy).

8080 nije otvoren u OCI security listi, pa se ide kroz UI koji je već izložen.
UI vraća HTML — iz njega se vadi stvarni brief.

    python3 fetch_real_briefs.py     # -> real_briefs.json
"""
import json
import re
import time
import urllib.parse
import urllib.request

INPUTS = [
    ("b.txt", "Server pada u ponoć. Tim izlazi na fix do 2 ujutro. "
              "Do jutra sve radi."),
    ("perf.txt", "Klijent žali da mu stranica otvara 8 sekundi. Uzrok je 40 "
                 "zatvorenih konekcija u poolu. Produkcija je na 500, ali "
                 "ljudi nisu primijetili."),
    ("conf.txt", "Konferencija je pomjerena na maj. RAN je završen, a dva "
                 "takmičara su odustala. Pobijedila je ekipa sa 22 godine "
                 "iskustva."),
]

UI = "http://92.5.41.244:8000/overnight/"


def ask(text):
    body = urllib.parse.urlencode({"text": text}).encode()
    req = urllib.request.Request(UI, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=180) as r:
        html = r.read().decode("utf-8", "replace")
    # briefovi su u <div class='out'> ... <div style='margin-bottom:.7rem'>• TEXT</div>
    m = re.search(r"margin-bottom:\.7rem'>([^<]+)</div>", html)
    if not m:
        m = re.search(r"<div class='out'>(.*?)</div>", html, re.S)
        if m:
            return re.sub(r"<[^>]+>", "", m.group(1)).strip()
        return "[nema odgovora]"
    return m.group(1).lstrip("• ").strip()


def main():
    out = []
    for name, text in INPUTS:
        t0 = time.time()
        try:
            brief = ask(text)
        except Exception as e:
            brief = f"[greška: {e}]"
        out.append({"name": name, "text": text, "brief": brief,
                    "secs": round(time.time() - t0, 1)})
        print(f"  {name}: {brief[:100]}  ({out[-1]['secs']}s)")
    with open("/home/redman8326/overnight/real_briefs.json", "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print("\nspremljeno -> real_briefs.json")


if __name__ == "__main__":
    main()
