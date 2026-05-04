import requests, re, json

HEADERS = {"User-Agent": "Mozilla/5.0"}
r = requests.get("https://www.skool.com/valueknow-9324/-/members", headers=HEADERS, timeout=10)

# Extract __NEXT_DATA__ JSON blob
match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', r.text)
if match:
    data = json.loads(match.group(1))
    print("NEXT_DATA found! Top-level keys:")
    print(list(data.keys()))
    props = data.get("props", {}).get("pageProps", {})
    print("pageProps keys:", list(props.keys()))
    print(json.dumps(props, indent=2)[:3000])
else:
    print("No __NEXT_DATA__ found")
    # Show raw snippet around 'member' keyword
    idx = r.text.lower().find("member")
    print(r.text[max(0, idx-200):idx+500])
