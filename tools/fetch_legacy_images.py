#!/usr/bin/env python3
"""Download the client's own images used by migrated legacy content.

Reads content/legacy/images.json (written by parse_legacy.py), downloads
each image, resizes to fit 1000x1000, converts to WebP and saves it under
public/assets/legacy/<yyyy>/<mm>/<name>.webp. Writes content/legacy/image-map.json
({original URL: local path}); the builder rewrites <img src> through it.
Resumable — existing outputs are skipped.

    python3 tools/fetch_legacy_images.py
"""
import io
import json
import os
import re
import sys
import subprocess
import tempfile
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIST = os.path.join(ROOT, 'content', 'legacy', 'images.json')
MAP = os.path.join(ROOT, 'content', 'legacy', 'image-map.json')
DEST = os.path.join(ROOT, 'public', 'assets', 'legacy')
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/128 Safari/537.36'
MAX = 1000
QUALITY = 74


def local_path(url):
    m = re.search(r'/wp-content/uploads/(\d{4})/(\d{2})/([^/]+)$', url)
    if not m:
        return None
    name = re.sub(r'\.(jpe?g|png|webp|avif|gif)$', '', m.group(3), flags=re.I)
    name = re.sub(r'[^A-Za-z0-9._-]+', '-', name)[:120]
    return f'/assets/legacy/{m.group(1)}/{m.group(2)}/{name}.webp'


def sips_decode(data):
    with tempfile.TemporaryDirectory() as d:
        src, dst = os.path.join(d, 'in'), os.path.join(d, 'out.png')
        open(src, 'wb').write(data)
        subprocess.run(['sips', '-s', 'format', 'png', src, '--out', dst], check=True, capture_output=True)
        im = Image.open(dst)
        im.load()
        return im


def fetch(url):
    rel = local_path(url)
    if not rel:
        return url, None, 'skip'
    out = os.path.join(ROOT, 'public', rel.lstrip('/'))
    if os.path.exists(out):
        return url, rel, 'cached'
    try:
        req = urllib.request.Request(urllib.parse.quote(url, safe=':/%'), headers={'User-Agent': UA})
        data = urllib.request.urlopen(req, timeout=60).read()
        try:
            im = Image.open(io.BytesIO(data))
        except Exception:  # noqa: BLE001 — e.g. AVIF, which this Pillow can't decode; macOS sips can
            im = sips_decode(data)
        if im.mode in ('P', 'LA'):
            im = im.convert('RGBA')
        elif im.mode not in ('RGB', 'RGBA'):
            im = im.convert('RGB')
        im.thumbnail((MAX, MAX), Image.LANCZOS)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        im.save(out, 'WEBP', quality=QUALITY, method=5)
        return url, rel, 'fetched'
    except Exception as e:  # noqa: BLE001 — 404s, AVIF the local Pillow can't read, etc.
        return url, None, f'error: {e}'


def main():
    urls = json.load(open(LIST))
    mapping = json.load(open(MAP)) if os.path.exists(MAP) else {}
    counts = {}
    with ThreadPoolExecutor(6) as pool:
        for i, (url, rel, status) in enumerate(pool.map(fetch, urls), 1):
            key = status.split(':')[0]
            counts[key] = counts.get(key, 0) + 1
            if rel:
                mapping[url] = rel
            elif status.startswith('error'):
                print(f'  {url}: {status}', file=sys.stderr)
            if i % 200 == 0:
                print(f'  {i}/{len(urls)} {counts}', flush=True)
    with open(MAP, 'w') as f:
        json.dump(mapping, f, indent=0, sort_keys=True)
    print(counts)


if __name__ == '__main__':
    main()
