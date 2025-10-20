# fetch_chaingpt_assets.py
# Automated Playwright script to render SPA and download assets (frontend only)

import os
import json
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "chaingpt_assets"
URL = "https://labs.chaingpt.org/"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def save_file(url, content):
    """Save asset to local folder structure."""
    parsed = urlparse(url)
    path = parsed.path.lstrip("/")
    local_path = os.path.join(OUTPUT_DIR, path)
    folder = os.path.dirname(local_path)
    os.makedirs(folder, exist_ok=True)
    with open(local_path, "wb") as f:
        f.write(content)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    print(f"Loading {URL} ...")
    page.goto(URL, wait_until="networkidle")

    # Save the rendered HTML
    html = page.content()
    with open(os.path.join(OUTPUT_DIR, "page_rendered.html"), "w", encoding="utf-8") as f:
        f.write(html)

    # Collect asset URLs
    urls = set()
    for tag in page.query_selector_all("link[href], script[src], img[src]"):
        src = tag.get_attribute("href") or tag.get_attribute("src")
        if src and (src.startswith("http") or src.startswith("/")):
            urls.add(src if src.startswith("http") else f"{URL.rstrip('/')}/{src.lstrip('/')}")

    print(f"Found {len(urls)} assets. Downloading...")

    downloaded = []
    for url in urls:
        try:
            resp = page.request.get(url)
            if resp.ok:
                save_file(url, resp.body())
                downloaded.append(url)
        except Exception as e:
            print(f"Failed: {url} ({e})")

    with open(os.path.join(OUTPUT_DIR, "downloaded_files.json"), "w") as f:
        json.dump(downloaded, f, indent=2)

    browser.close()
    print(f"✅ Done. Assets saved to: {OUTPUT_DIR}")
