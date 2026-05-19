import requests
import re
import json

HEADERS = {"User-Agent": "Mozilla/5.0"}
BASE_URL = "https://www.skool.com/valueknow-9324/-/members"
NEXT_DATA_PATTERN = re.compile(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.DOTALL)

def scrape_all_pages() -> set:
    names = set()
    page = 1
    while True:
        url = f"{BASE_URL}?p={page}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            match = NEXT_DATA_PATTERN.search(r.text)
            if not match:
                print(f"[scraper] No __NEXT_DATA__ found on page {page}, stopping.")
                break
            data = json.loads(match.group(1))
            users = data.get("props", {}).get("pageProps", {}).get("users", [])
            if not users:
                break
            for user in users:
                first = user.get("firstName", "").strip()
                last = user.get("lastName", "").strip()
                full = f"{first} {last}".strip()
                if full:
                    names.add(full)
            total_pages = data.get("props", {}).get("pageProps", {}).get("totalPages", 1)
            if page >= total_pages:
                break
            page += 1
        except Exception as e:
            print(f"[scraper] Error on page {page}: {e}")
            break
    print(f"[scraper] {len(names)} names loaded")
    return names

