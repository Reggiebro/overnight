import json
import urllib.error
import urllib.request

KEY = "1CQNsLPBTPKtRF6RCRCNXSxp"
ID = 4901213
body = open("/home/redman8326/overnight/HACKTOBERFEST_POST.md").read()

payload = {
    "article": {
        "body_markdown": body,
    }
}

req = urllib.request.Request(
    f"https://dev.to/api/articles/{ID}",
    data=json.dumps(payload).encode(),
    headers={
        "api-key": KEY,
        "Referer": "https://dev.to",
        "Origin": "https://dev.to",
        "Content-Type": "application/json",
        "User-Agent": "overnight-update/1.0",
    },
    method="PUT",
)

try:
    with urllib.request.urlopen(req, timeout=90) as r:
        d = json.loads(r.read().decode())
    print("STATUS", r.status)
    print("URL", d.get("url"))
    print("TITLE", d.get("title"))
    print("edited_at", d.get("edited_at"))
except urllib.error.HTTPError as e:
    print("HTTPError", e.code)
    print(e.read().decode()[:2000])
