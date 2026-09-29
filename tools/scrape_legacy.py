#!/usr/bin/env python3
"""Download every page and post from the legacy WordPress site (skycleanair.com).

Two steps, both resumable (rerun and it only fetches what's missing):

1. Metadata (id, URL, title, dates, parent, categories) for every page and
   post, from the WP REST API with content excluded — content-rendering API
   calls take ~7s each on their server and time out in batches.
2. The public HTML of each URL. The front end is page-cached (~1s/page) and
   also carries the Rank Math SEO title + meta description the API lacks.

Raw HTML is ~1GB, so it's cached gzipped OUTSIDE the repo/iCloud folder, in
~/Library/Caches/sky-clean-air/legacy-raw/ (override with LEGACY_CACHE=...).
Metadata goes to content/legacy/meta/ (committed).

    python3 tools/scrape_legacy.py            # fetch anything not cached yet
    python3 tools/scrape_legacy.py --refresh  # re-download everything

Then run tools/parse_legacy.py.
"""
import gzip
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META = os.path.join(ROOT, 'content', 'legacy', 'meta')
CACHE = os.environ.get('LEGACY_CACHE', os.path.expanduser('~/Library/Caches/sky-clean-air/legacy-raw'))
API = 'https://skycleanair.com/wp-json/wp/v2'
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/128 Safari/537.36'
WORKERS = 4  # be gentle with the client's live server
FIELDS = {
    'pages': 'id,slug,link,parent,date,modified,title,featured_media',
    'posts': 'id,slug,link,date,modified,title,featured_media,categories',
    'categories': 'id,slug,name,count,parent',
}


def fetch(url, tries=6, binary=False):
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                body = r.read()
                return (body if binary else body.decode('utf-8')), r.headers
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None, None
            err = e
        except Exception as e:  # noqa: BLE001 — timeouts, resets
            err = e
        wait = 2 ** attempt
        print(f'  retry {attempt + 1}/{tries} in {wait}s ({url}): {err}', file=sys.stderr)
        time.sleep(wait)
    raise RuntimeError(f'giving up on {url}')


def fetch_meta(kind):
    items, page = [], 1
    while True:
        body, headers = fetch(f'{API}/{kind}?per_page=100&page={page}&_fields={FIELDS[kind]}')
        items += json.loads(body)
        if page >= int(headers.get('X-WP-TotalPages', 1)):
            break
        page += 1
    with open(os.path.join(META, f'{kind}.json'), 'w') as f:
        json.dump(items, f, indent=0, ensure_ascii=False)
    return items


def fetch_html(kind, item, refresh):
    path = os.path.join(CACHE, kind, f'{item["id"]}.html.gz')
    if os.path.exists(path) and not refresh:
        return 'cached'
    body, _ = fetch(item['link'], binary=True)
    if body is None:
        return 'missing'
    with gzip.open(path, 'wb') as f:
        f.write(body)
    return 'fetched'


def main():
    refresh = '--refresh' in sys.argv
    os.makedirs(META, exist_ok=True)
    for kind in ('categories', 'pages', 'posts'):
        path = os.path.join(META, f'{kind}.json')
        if os.path.exists(path) and not refresh:
            items = json.load(open(path))
        else:
            items = fetch_meta(kind)
        print(f'{kind}: {len(items)} items in metadata')
        if kind == 'categories':
            continue
        os.makedirs(os.path.join(CACHE, kind), exist_ok=True)
        counts = {}
        with ThreadPoolExecutor(WORKERS) as pool:
            for i, result in enumerate(pool.map(lambda it: fetch_html(kind, it, refresh), items), 1):
                counts[result] = counts.get(result, 0) + 1
                if i % 100 == 0:
                    print(f'  {kind}: {i}/{len(items)} {counts}', flush=True)
        print(f'  {kind} done: {counts}')


if __name__ == '__main__':
    main()
