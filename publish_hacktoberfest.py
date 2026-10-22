import json
import urllib.error
import urllib.request

KEY = "1CQNsLPBTPKtRF6RCRCNXSxp"
body = open("/home/redman8326/overnight/HACKTOBERFEST_POST.md").read()

payload = {
    "article": {
        "title": "I Built an Agent That Reads So I Don't Have To",
        "body_markdown": body,
        "published": True,
        "tags": ["devchallenge", "hf26challenge"],
        "description": ("Overnight runs a local open-weight model on my own machine, reads "
                        "everything I point it at, and hands me a two-line brief in the "
                        "morning. No API key, no cloud, no bill. Here is why that is the point."),
    }
}

req = urllib.request.Request(
    "https://dev.to/api/articles",
    data=json.dumps(payload).encode(),
    headers={
        "api-key": KEY,
        "Referer": "https://dev.to",
        "Origin": "https://dev.to",
        "Content-Type": "application/json",
        "User-Agent": "overnight-submission/1.0",
    },
    method="POST",
)

try:
    with urllib.request.urlopen(req, timeout=90) as r:
        d = json.loads(r.read().decode())
    print("STATUS", r.status)
    print("URL", d.get("url"))
    print("ID", d.get("id"))
    print("TAGS", d.get("tags"))
    print("PUBLISHED", d.get("published"))
except urllib.error.HTTPError as e:
    print("HTTPError", e.code)
    print(e.read().decode()[:3000])
except Exception as e:
    print("ERR", type(e).__name__, e)
