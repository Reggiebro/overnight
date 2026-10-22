import json
import urllib.request

API = "https://dev.to/api"


def get(path):
    req = urllib.request.Request(f"{API}{path}", headers={
        "api-key": "1CQNsLPBTPKtRF6RCRCNXSxp",
        "Referer": "https://dev.to",
        "User-Agent": "audit/1.0"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())


targets = {
    4890855: "cryocooler (55)",
    4892006: "slothd (46)",
    4882857: "topics (44)",
}

for aid, label in targets.items():
    a = get(f"/articles/{aid}")
    body = a.get("body_markdown") or ""
    print("=" * 78)
    print(f"{label}  ->  {a.get('title')}")
    print(f"url: {a.get('url')}")
    print(f"reading_time: {a.get('reading_time_minutes')} min | "
          f"len: {len(body)} | reactions: {a.get('positive_reactions_count')}")
    print(f"tags: {a.get('tags')}")
    print("--- prvih 2200 znakova ---")
    print(body[:2200])
    print()
    # sekcije
    import re
    secs = re.findall(r"^##\s+(.+)$", body, re.M)
    print("--- sekcije:", secs)
    print()
