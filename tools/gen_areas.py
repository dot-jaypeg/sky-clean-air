"""Service-area pages: /service-areas/ hub, one page per region, one per city.

Everything is driven by src/data/areas.json, so a new market is a data
change, not a code change:
  - Regions render in `order` (Orange County first — it's the market the
    client is actively launching).
  - A city gets its own page when its effective status (its own `status`,
    else its region's) is not `coming-soon`. Coming-soon cities still show
    as gray pins and in the text lists, so the keywords are on the page.
  - City copy: migrated legacy copy (San Diego neighborhoods) or the
    hand-written intro in src/data/area-copy.json, plus generated sections
    (services offered there, nearby areas, map).
"""
import json
import math
import os

import components
from gen_legacy import (article_layout, faq_section, image_map, legacy_all, legacy_by_path, local_images,
                        seo_title, sidebar, strip_self_links)
from sitelib import DATA_DIR, breadcrumb_schema, cta_band, esc, icon, page_hero

MAP_ASSETS = '<link rel="stylesheet" href="/vendor/leaflet/leaflet.css">\n'
MAP_SCRIPTS = '<script src="/vendor/leaflet/leaflet.js"></script>\n<script src="/js/map.js"></script>'


def area_copy():
    p = os.path.join(DATA_DIR, 'area-copy.json')
    return json.load(open(p)) if os.path.exists(p) else {}


def status(D, c):
    return c.get('status') or D.region(c['region'])['status']


def live(D, c):
    return status(D, c) != 'coming-soon'


def dist(a, b):
    # Rough km distance; fine for "nearby" ordering.
    return math.hypot((a['lat'] - b['lat']) * 111, (a['lng'] - b['lng']) * 92)


def map_block(D, pins, center=None, zoom=None, cls='', legend=True, filters=False):
    cfg = {'tiles': D.areas['map']['tiles'], 'pins': pins, 'maxZoom': 13}
    if center:
        cfg['center'], cfg['zoom'] = center, zoom
    filt = ''
    if filters:
        btns = ''.join(f'<button type="button" data-map-region="{r["slug"]}">{esc(r["name"])}</button>' for r in D.regions)
        filt = f'<div class="map-filters"><button type="button" class="active" data-map-region="all">All Areas</button>{btns}</div>'
    leg = ''
    if legend:
        leg = ('<div class="map-legend"><span><i class="dot active"></i> Serving now</span>'
               '<span><i class="dot launching"></i> Newly launched</span>'
               '<span><i class="dot soon"></i> Coming soon</span></div>')
    return f'''<div class="area-map-wrap {cls}">
  {filt}
  <div class="area-map" data-area-map role="region" aria-label="Map of Sky Clean Air service areas"></div>
  {leg}
  <script type="application/json" id="map-data">{json.dumps(cfg, ensure_ascii=False)}</script>
</div>'''


def pin(D, c, current=False):
    r = D.region(c['region'])
    p = {'name': c['name'], 'lat': c['lat'], 'lng': c['lng'], 'status': status(D, c),
         'region': r['name'], 'regionSlug': r['slug']}
    if live(D, c):
        p['href'] = f'/service-areas/{c["slug"]}/'
    if current:
        p['current'] = True
    return p


def city_links(D, cities, cls='area-list'):
    items = []
    for c in cities:
        if live(D, c):
            items.append(f'<li><a href="/service-areas/{c["slug"]}/">{esc(c["name"])}</a></li>')
        else:
            items.append(f'<li><span>{esc(c["name"])}</span></li>')
    return f'<ul class="{cls}">{"".join(items)}</ul>'


def region_card(D, r):
    cities = D.cities(r['slug'])
    badge = f'<span class="region-badge">{esc(r["badge"])}</span>' if r.get('badge') else ''
    towns = [c for c in cities if c['type'] == 'city']
    hoods = [c for c in cities if c['type'] == 'neighborhood']
    hoods_html = ''
    if hoods:
        hoods_html = f'<details class="hood-more"><summary>San Diego neighborhoods ({len(hoods)})</summary>{city_links(D, hoods, "area-list compact")}</details>'
    return f'''<div class="region-card region-{r["status"]}" id="{r["slug"]}">
  <div class="region-card-head">
    <h2><a href="/service-areas/{r["slug"]}/">{esc(r["name"])}</a></h2>{badge}
  </div>
  <p>{esc(r["blurb"])}</p>
  {city_links(D, towns)}
  {hoods_html}
  <a class="service-link" href="/service-areas/{r["slug"]}/">{"Learn about " + esc(r["name"]) if r["status"] != "coming-soon" else "See what's coming"} &rarr;</a>
</div>'''


def hub(site):
    D, ch = site.D, site.ch
    pins = [pin(D, c) for c in D.cities()]
    live_count = sum(1 for c in D.cities() if live(D, c))
    crumbs = [('Home', '/'), ('Service Areas', None)]
    cards = ''.join(region_card(D, r) for r in D.regions)
    site.add({
        'path': '/service-areas/',
        'title': 'Service Areas: Orange County, San Diego & Inland Empire | Sky Clean Air',
        'description': f'Sky Clean Air serves {live_count}+ communities across Orange County and San Diego County, with the Inland Empire coming soon. Find your city on our service area map.',
        'head_extra': MAP_ASSETS, 'scripts': MAP_SCRIPTS,
        'schema': [breadcrumb_schema(D.site['domain'], crumbs)],
        'body': page_hero(ch, 'Where We <span class="hl">Work</span>',
                          'Orange County, San Diego County and — soon — the Inland Empire. Find your city below, or just call; if we can get to you, we will.',
                          crumbs) +
                f'''<section class="section map-section" id="map"><div class="container">
  <div class="section-head center"><h2>Our <span class="grad-text">Service Area</span> Map</h2>
  <p>Every dot is a community we serve. Tap one to see local details.</p></div>
  {map_block(D, pins, filters=True)}
</div></section>
<section class="section bg-soft"><div class="container"><div class="region-cards">{cards}</div>
<p class="area-cta-note">Don't see your city? Call <a href="{ch.tel}">{ch.phone}</a> — we're adding new areas as we grow.</p></div></section>''' +
                cta_band(ch),
    })


def region_pages(site):
    D, ch = site.D, site.ch
    for r in D.regions:
        cities = D.cities(r['slug'])
        path = f'/service-areas/{r["slug"]}/'
        crumbs = [('Home', '/'), ('Service Areas', '/service-areas/'), (r['name'], None)]
        towns = [c for c in cities if c['type'] == 'city']
        hoods = [c for c in cities if c['type'] == 'neighborhood']
        soon = r['status'] == 'coming-soon'
        intro = ''.join(f'<p>{esc(p)}</p>' for p in r.get('intro', [r['blurb']]))
        lists = f'<h2>Cities We Serve in {esc(r["name"])}</h2>{city_links(D, towns, "area-list cols")}'
        if hoods:
            lists += f'<h2>San Diego Neighborhoods</h2>{city_links(D, hoods, "area-list cols compact")}'
        services = '' if soon else f'''<section class="section bg-soft"><div class="container">
  <div class="section-head center"><h2>Services in <span class="grad-text">{esc(r["name"])}</span></h2></div>
  {components.services_grid(ch, D)}</div></section>'''
        kicker = esc(r.get('badge') or f'{len([c for c in cities if live(D, c)])} communities')
        h1 = f'HVAC &amp; Air Quality Services in <span class="hl">{esc(r["name"])}</span>'
        if soon:
            h1 = f'<span class="hl">{esc(r["name"])}</span> — Coming Soon'
        site.add({
            'path': path,
            'title': (f'{r["name"]} HVAC, Air Duct & Dryer Vent Services | Sky Clean Air' if not soon
                      else f'Sky Clean Air in the {r["name"]} — Coming Soon'),
            'description': r['blurb'],
            'head_extra': MAP_ASSETS, 'scripts': MAP_SCRIPTS,
            'schema': [breadcrumb_schema(D.site['domain'], crumbs)],
            'body': page_hero(ch, h1, esc(r['blurb']), crumbs, kicker=kicker) +
                    f'''<section class="section"><div class="container region-layout">
  <div class="region-copy prose">{intro}{lists}</div>
  <div class="region-map">{map_block(D, [pin(D, c) for c in cities], legend=soon or r["status"] == "launching")}</div>
</div></section>''' + services +
                    (f'<section class="section"><div class="container"><div class="section-head center"><h2>What Our <span class="grad-text">Customers</span> Say</h2></div>{components.reviews(ch, D, "2")}</div></section>' if not soon else '') +
                    cta_band(ch),
        })


def services_here(D, c, existing):
    """Category → service links for a city, pointing at the local page when one exists."""
    cols = []
    for cat in D.categories:
        if cat['slug'] == 'commercial':
            continue
        items = []
        for s in [s for s in cat['services'] if not s.get('hidden')][:5]:
            local = f'/{s["slug"]}/{c["slug"]}/'
            href = local if local in existing else f'/{s["slug"]}/'
            items.append(f'<li><a href="{href}">{esc(s["name"])}</a></li>')
        cols.append(f'<div class="svc-col"><h3><a href="/services/{cat["slug"]}/">{esc(cat["name"])}</a></h3><ul>{"".join(items)}</ul></div>')
    return f'<div class="svc-cols">{"".join(cols)}</div>'


def city_pages(site):
    D, ch = site.D, site.ch
    copy = area_copy()
    existing = {r['path'] for r in legacy_all('page', 'service-location')}
    all_cities = D.cities()
    for c in all_cities:
        if not live(D, c):
            continue
        path = f'/service-areas/{c["slug"]}/'
        r = D.region(c['region'])
        legacy = legacy_by_path(path)
        cc = copy.get(c['slug'])
        name = c['name']
        crumbs = [('Home', '/'), ('Service Areas', '/service-areas/'), (r['name'], f'/service-areas/{r["slug"]}/'), (name, None)]
        nearby = sorted((o for o in all_cities if o is not c and live(D, o)), key=lambda o: dist(c, o))[:10]
        # Main copy
        faqs = []
        if cc:
            local = ''.join(f'<li>{esc(x)}</li>' for x in cc.get('local', []))
            hoods = cc.get('neighborhoods', [])
            main = ''.join(f'<p>{esc(p)}</p>' for p in cc['intro'])
            if local:
                main += f'<h2>What We See in {esc(name)} Homes</h2><ul>{local}</ul>'
            if hoods:
                main += f'<p class="hood-line"><strong>Neighborhoods we serve in {esc(name)}:</strong> {esc(", ".join(hoods))}, and surrounding areas.</p>'
            desc = f'HVAC, air duct cleaning, dryer vent, attic insulation and indoor air quality services in {name}, CA. Family-owned Sky Clean Air — call {ch.phone} for a free estimate.'
            title = f'HVAC & Air Duct Cleaning in {name}, CA | Sky Clean Air'
        elif legacy:
            main = strip_self_links(local_images(legacy['body']), path)
            faqs = legacy['faqs']
            desc = legacy['description'] or f'HVAC and indoor air quality services in {name}, CA.'
            title = seo_title(legacy, f'HVAC & Air Duct Services in {name}, CA')
        else:
            main = (f'<p>Sky Clean Air provides HVAC installation and repair, air duct and dryer vent cleaning, attic insulation '
                    f'and indoor air quality services to homes and businesses in {esc(name)} and across {esc(r["name"])}.</p>')
            desc = f'HVAC and indoor air quality services in {name}, CA from family-owned Sky Clean Air.'
            title = f'HVAC & Air Duct Services in {name}, CA | Sky Clean Air'
        if r['status'] == 'coming-soon' or c.get('status'):
            main = (f'<div class="callout"><strong>Now taking select jobs in {esc(name)}.</strong> Full {esc(r["name"])} service is coming soon — '
                    f'call <a href="{{{{tel}}}}">{{{{phone}}}}</a> and we\'ll let you know if we can schedule you.</div>') + main
        faq_html, faq_schema = faq_section(faqs, f'{name} HVAC &amp; Air Quality FAQs')
        extra = f'''<section class="city-services"><h2>Services in {esc(name)}</h2>{services_here(D, c, existing)}</section>
<section class="city-nearby"><h2>Nearby Areas We Serve</h2><div class="city-cloud">{"".join(f'<a class="city-chip light" href="/service-areas/{o["slug"]}/">{esc(o["name"])}</a>' for o in nearby)}</div></section>'''
        side_map = f'<div class="side-card side-map"><h3>{esc(name)} on the Map</h3>{map_block(D, [pin(D, o) for o in nearby] + [pin(D, c, True)], center=[c["lat"], c["lng"]], zoom=12 if c["type"] == "neighborhood" else 11, cls="mini", legend=False)}</div>'
        side = sidebar(ch, D, f'More in {r["name"]}', [(o['name'], f'/service-areas/{o["slug"]}/') for o in nearby[:6]], extra=side_map)
        place_schema = {
            '@context': 'https://schema.org', '@type': 'Service', 'serviceType': 'HVAC and indoor air quality services',
            'provider': {'@type': 'HVACBusiness', 'name': D.site['name'], 'telephone': '+1-' + D.site['phone']},
            'areaServed': {'@type': 'City' if c['type'] == 'city' else 'Place', 'name': f'{name}, CA',
                           'geo': {'@type': 'GeoCoordinates', 'latitude': c['lat'], 'longitude': c['lng']}},
        }
        img = image_map().get((legacy or {}).get('image') or '')
        site.add({
            'path': path, 'legacy': bool(legacy and not cc), 'lastmod': (legacy or {}).get('modified'),
            'title': title, 'description': desc,
            'og_image': img or '/assets/images/story-team.jpg',
            'head_extra': MAP_ASSETS, 'scripts': MAP_SCRIPTS,
            'schema': [place_schema, breadcrumb_schema(D.site['domain'], crumbs)] + faq_schema,
            'body': page_hero(ch, f'HVAC &amp; Air Duct Services in <span class="hl">{esc(name)}, CA</span>',
                              f'Family-owned heating, cooling, duct, dryer vent, attic and indoor air quality service for {esc(name)} homes and businesses.',
                              crumbs, kicker=esc(r['name'])) +
                    article_layout(f'<div class="prose">{main}</div>{extra}{faq_html}', side) +
                    cta_band(ch),
        })
