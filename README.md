# UNSW Thesis Topic With Better Filters and Flexibility

A small toolkit for pulling the list of thesis topics from the UNSW CSE Thesis Management System ([thesis.cse.unsw.edu.au](https://thesis.cse.unsw.edu.au/)) and turning it into a plain list of titles you can read, search and filter.

| File | What it does |
|---|---|
| `scrape_tms.py` | Opens the site in an invisible browser, captures the thesis data the site loads, and saves it to `thesis_projects.json`. |
| `extract_titles.py` | Reads `thesis_projects.json` and prints the topic titles, optionally filtered by thesis type. |

No UNSW login is needed.

---

## How it works

The thesis site is a JavaScript single-page app. Its `/search` page doesn't exist on the server; it only exists inside the app, so a plain web request gets a 404 or an empty page. `scrape_tms.py` works around this by driving a real browser (Chromium, controlled by [Playwright](https://playwright.dev/python/)):

1. It loads the site's home page and lets the app start up.
2. It navigates inside the app to the search view, like a user clicking a link.
3. It records the JSON data the app downloads in the background and saves it.

`extract_titles.py` then reads the saved data and prints the titles, so you only need to scrape once and can filter as often as you like.

---

## Setup

You need **Python 3.8+**.

```bash
pip install playwright
playwright install chromium
```

The second command downloads the Chromium browser that Playwright controls. It only needs to run once.

> On some Linux systems pip refuses to install into the system Python. Either use a virtual environment (`python -m venv .venv && source .venv/bin/activate`) or add `--break-system-packages` to the pip command.

---

## Usage

### 1. Scrape the site

```bash
python scrape_tms.py
```

This takes 10–20 seconds. On success you'll see:

```
Captured 3 API response(s) -> thesis_projects.json
```

It also writes `rendered_page.html`, a snapshot of the page the browser ended up showing, which is useful for debugging.

Re-run this whenever you want fresh data; topics change each term.

### 2. List the titles

```bash
python extract_titles.py
```

Every title prints one per line, followed by a summary like:

```
Total: 214 titles (of 214 captured topics; thesis_type values seen: Project, Research)
```

The summary lists the thesis types found in the data, which tells you exactly what you can filter on (see below).

---

## Filtering your results

### By thesis type

Add your own filters / changes in the topic extract line.

### By keyword

The titles print as plain lines, so standard command-line tools work on them.

**macOS / Linux:**

```bash
# Titles mentioning "learning" (case-insensitive)
python extract_titles.py | grep -i learning

# Research topics about security OR privacy
python extract_titles.py --type Research | grep -iE "security|privacy"

# Everything except blockchain topics
python extract_titles.py | grep -iv blockchain
```

**Windows (PowerShell):**

```powershell
python extract_titles.py | Select-String -Pattern "learning"
python extract_titles.py --type Research | Select-String -Pattern "security|privacy"
```

### Save the results to a file

```bash
python extract_titles.py --type Research > research_topics.txt
```

Only the titles go into the file; the "Total" summary still shows in your terminal.
---

## Going further: other fields and site-side filters

**Other fields.** Each topic in `thesis_projects.json` usually has more than a title (for example supervisor, description or area, depending on what the site returns). Open the file in a text editor or VS Code to see which fields exist. To print one alongside the title, edit this line in `extract_titles.py`:

```python
titles.append(title)
```

to something like:

```python
titles.append(f"{title}  —  {topic.get('supervisor', '')}")
```

replacing `supervisor` with a field name you actually see in the file.

**Filtering on the site itself.** `scrape_tms.py` requests an empty search with no filters so that it gets everything. The request is set in this line:

```python
history.pushState({}, '', '/search?search_query=&show_tagged=false&filters=%7B%7D');
```

You can put a keyword after `search_query=` (for example `search_query=robotics`) to have the site do the filtering. The `filters` value is URL-encoded JSON (`%7B%7D` is `{}`). To see what filters the site accepts, open the site in Chrome, apply a filter in the UI, and copy the resulting URL from the address bar. In most cases it's simpler to scrape everything once and filter locally as shown above.

---

## Troubleshooting

**"No matching API responses captured automatically."**
The app didn't load its data. Try:
- Open `rendered_page.html` in a browser to see what the scraper saw.
- In `scrape_tms.py`, change `headless=True` to `headless=False` and run again to watch the browser.
- Open the site in Chrome, press F12, go to **Network → Fetch/XHR**, run a search, and note the request the page makes. You can then adjust the scraper or call that URL directly.

**"No response containing a 'topics' list found"**
The scrape captured something, but not the topic list, or the site now uses a different field name. Open `thesis_projects.json` and look for the list of topics. If it's under a different key, update `"topics"` in `iter_topics()` in `extract_titles.py`.

**The total looks lower than on the website.**
The site may load results a page at a time, in which case only the first page is captured. Check the API request in DevTools for a `page` or `offset` parameter.

**`playwright: command not found`**
Run `python -m playwright install chromium` instead.

---

## Be considerate

This tool loads the site the same way a single visitor would. Run it occasionally rather than in a tight loop, and don't redistribute the scraped data outside of UNSW without checking that's allowed.
