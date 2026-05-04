import requests
import re

HEADERS = {"User-Agent": "Mozilla/5.0"}
BASE_URL = "https://www.skool.com/valueknow-9324/-/members"
PATTERN = re.compile(r'(.+)\n@')

def scrape_all_pages() -> set:
    names = set()
    page = 1
    while True:
        url = BASE_URL if page == 1 else f"{BASE_URL}?p={page}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            text = r.text.replace('\r\n', '\n').replace('\r', '\n')
            found = PATTERN.findall(text)
            if not found:
                break
            for name in found:
                clean = name.strip()
                if clean:
                    names.add(clean)
            page += 1
        except Exception as e:
            print(f"[scraper] Error on page {page}: {e}")
            break
    print(f"[scraper] {len(names)} names loaded")
    return names
