import json
import re
import time
import urllib.parse
import urllib.request

UI = "http://92.5.41.244:8000/overnight/"

# Engleski ulazi — model je engleski-treniran, tako da engleski ulaz daje
# čistiji brief. Prikazujemo stvarni rad, samo na jeziku na kojem model dobro radi.
INPUTS = [
    ("alerts.txt", "The alert fired twice in the last hour. The on-call engineer "
                   "acknowledged it but the volume is still climbing. Yesterday's "
                   "incident took three hours to resolve because nobody could find "
                   "the runbook."),
    ("changelog.txt", "Version 2.4 removed the legacy export endpoint. Existing "
                      "integrations using /v1/export will return 410 Gone. The "
                      "replacement endpoint ships in 2.5 and requires a new auth "
                      "header. Migration guide is in the repo."),
]


def ask(text):
    body = urllib.parse.urlencode({"text": text}).encode()
    req = urllib.request.Request(UI, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=180) as r:
        html = r.read().decode("utf-8", "replace")
    m = re.search(r"margin-bottom:\.7rem'>([^<]+)</div>", html)
    if m:
        return m.group(1).lstrip("• ").strip()
    m = re.search(r"<div class='out'>(.*?)</div>", html, re.S)
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    return "[nema odgovora]"


out = []
for name, text in INPUTS:
    t0 = time.time()
    brief = ask(text)
    out.append({"name": name, "text": text, "brief": brief,
                "secs": round(time.time() - t0, 1)})
    print(f"{name}:\n  {brief}\n  ({out[-1]['secs']}s)\n")

json.dump(out, open("/home/redman8326/overnight/real_briefs.json", "w"),
          indent=2, ensure_ascii=False)
print("snimljeno")
