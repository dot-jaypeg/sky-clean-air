#!/usr/bin/env python3
"""Fill in lat/lng for any city in src/data/areas.json that doesn't have one.

Uses OpenStreetMap's Nominatim geocoder (free, 1 request/second limit).
Only cities missing coordinates are looked up, so after adding a new market
to areas.json just run:

    python3 tools/geocode_areas.py

Anything Nominatim can't find is reported — add its lat/lng by hand.
"""
import json
import os
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'src', 'data', 'areas.json')
UA = 'SkyCleanAirSiteBuilder/1.0 (jayden@advancedmarketers.co)'
# Region slug -> county name used in the geocoder query. Add an entry when adding a region.
COUNTY = {'orange-county': 'Orange County', 'san-diego-county': 'San Diego County'}
# Southern California bounding box — rejects same-named places elsewhere.
VIEWBOX = '-118.2,34.1,-116.0,32.5'


def lookup(q):
    url = 'https://nominatim.openstreetmap.org/search?' + urllib.parse.urlencode(
        {'q': q, 'format': 'json', 'limit': 1, 'countrycodes': 'us', 'viewbox': VIEWBOX, 'bounded': 1})
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        res = json.loads(r.read())
    time.sleep(1.1)
    return (round(float(res[0]['lat']), 4), round(float(res[0]['lon']), 4)) if res else None


def main():
    data = json.load(open(PATH))
    missing = []
    for c in data['cities']:
        if 'lat' in c:
            continue
        queries = ([f'{c["name"]}, San Diego, California', f'{c["name"]}, San Diego County, California']
                   if c['type'] == 'neighborhood' else [f'{c["name"]}, {COUNTY[c["region"]]}, California'])
        hit = None
        for q in queries:
            hit = lookup(q)
            if hit:
                break
        if hit:
            c['lat'], c['lng'] = hit
            print(f'{c["slug"]}: {hit}')
        else:
            missing.append(c['slug'])
            print(f'{c["slug"]}: NOT FOUND')
        with open(PATH, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    if missing:
        print('\nAdd coordinates by hand for:', ', '.join(missing))


if __name__ == '__main__':
    main()
