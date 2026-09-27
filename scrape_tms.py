"""
Scraper for thesis.cse.unsw.edu.au (UNSW CSE Thesis Management System)

No login is required, but the site is a client-rendered single-page app.
Requesting the URL /search directly (a fresh HTTP GET, like a plain
`requests.get` or a browser reload of that exact address) returns a 404,
because the server has no route configured for that path — it only exists
as a client-side (JS pushState) route inside the app.

So the trick is: load the app's root page first (which the server *does*
serve), let the JS boot up, then trigger the in-app navigation to the
search view — exactly like a real user clicking around — and capture the
underlying API calls the app makes to fetch project data.

Install first:
    pip install playwright --break-system-packages
    playwright install chromium

Usage:
    python scrape_tms.py
"""

import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "https://thesis.cse.unsw.edu.au/"
OUTPUT_FILE = Path("thesis_projects.json")


def scrape():
    captured_responses = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Intercept network responses so we can find the underlying JSON API
        # the frontend calls, rather than scraping rendered HTML by hand.
        def handle_response(response):
            url = response.url
            ct = response.headers.get("content-type", "")
            if "application/json" in ct and ("api" in url or "search" in url or "project" in url or "topic" in url):
                try:
                    captured_responses.append({"url": url, "data": response.json()})
                except Exception:
                    pass

        page.on("response", handle_response)

        # Step 1: load the real root page (this one the server serves fine).
        page.goto(BASE_URL, wait_until="networkidle")

        # Step 2: navigate WITHIN the app to the search view, using pushState,
        # so the browser doesn't make a fresh server request for /search.
        # This mirrors what happens when a real user clicks a "Search" link.
        page.evaluate(
            """() => {
                history.pushState({}, '', '/search?search_query=&show_tagged=false&filters=%7B%7D');
                window.dispatchEvent(new PopStateEvent('popstate'));
            }"""
        )

        # Give the SPA a moment to react to the route change and fire its
        # data-fetching calls.
        page.wait_for_timeout(3000)
        try:
            page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass

        # Fallback: if the app didn't react to a synthetic popstate (some
        # routers listen for their own custom events instead), try clicking
        # an actual on-page element. Adjust the selector after inspecting
        # the page yourself (right-click > Inspect on the search/nav link).
        if not captured_responses:
            try:
                page.click("text=Search", timeout=3000)
                page.wait_for_timeout(3000)
            except Exception:
                pass

        # Also grab the rendered HTML as a fallback / for manual inspection.
        html = page.content()
        Path("rendered_page.html").write_text(html)

        browser.close()

    if captured_responses:
        OUTPUT_FILE.write_text(json.dumps(captured_responses, indent=2))
        print(f"Captured {len(captured_responses)} API response(s) -> {OUTPUT_FILE}")
        print("Inspect this file to find which one holds the actual project list.")
        print("Once you know the endpoint + params, you can likely call it")
        print("directly with `requests` for future scrapes — no browser needed.")
    else:
        print("No matching API responses captured automatically.")
        print("Saved the rendered DOM to rendered_page.html for inspection.")
        print("Open thesis.cse.unsw.edu.au in Chrome, open DevTools > Network > Fetch/XHR,")
        print("type a search, and note the exact request URL used — then either")
        print("adjust the click selector above, or call that endpoint directly.")


if __name__ == "__main__":
    scrape()
