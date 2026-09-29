"""Service pages, category hubs and the /services/ index.

Page copy, in priority order:
  1. src/content/services/<slug>.html — hand-written copy (front matter:
     title, description, h1, lede; body HTML). A trailing
     <h2>…FAQ…</h2> section of <h3>question</h3><p>answer</p> pairs is
     lifted out into the FAQ accordion + FAQPage schema.
  2. The migrated legacy copy for the same URL.
Category hubs can likewise have src/content/services/_<category>.html.
"""
import os
import re

import components
from gen_legacy import (area_name, article_layout, faq_section, image_map, legacy_all, legacy_by_path,
                        local_images, seo_title, sidebar, strip_self_links, text_excerpt)
from sitelib import ROOT, breadcrumb_schema, cta_band, esc, icon, page_hero

CONTENT = os.path.join(ROOT, 'src', 'content', 'services')


def custom_copy(name):
    path = os.path.join(CONTENT, f'{name}.html')
    if not os.path.exists(path):
        return None
    from build import parse_source
    p = parse_source(path)
    body, faqs = split_faqs(p['body'].strip())
    p['body'], p['faqs'] = body, faqs
    return p


def split_faqs(body):
    m = re.search(r'<h2>[^<]*(FAQ|Frequently Asked|Questions)[^<]*</h2>\s*(.*)$', body, re.I | re.S)
    if not m:
        return body, []
    pairs = re.findall(r'<h3>(.*?)</h3>\s*((?:<p>.*?</p>\s*|<ul>.*?</ul>\s*)+)', m.group(2), re.S)
    if not pairs:
        return body, []
    return body[:m.start()].rstrip(), [[re.sub(r'<[^>]+>', '', q).strip(), a.strip()] for q, a in pairs]


def locations_for(slug):
    """Neighborhood pages that exist for a service: [(area_slug, path)]."""
    out = []
    for r in legacy_all('page', 'service-location'):
        s, a = r['path'].strip('/').split('/')
        if s == slug:
            out.append((a, r['path']))
    return sorted(out)


def service_pages(site):
    D, ch = site.D, site.ch
    for cat, svc in D.all_services():
        slug = svc['slug']
        path = f'/{slug}/'
        legacy = legacy_by_path(path)
        custom = custom_copy(slug)
        name = svc['name']
        regions = [r['name'] for r in D.regions if r['status'] != 'coming-soon']
        if custom:
            h1 = custom.get('h1') or f'{name} in <span class="hl">San Diego &amp; Orange County</span>'
            lede = custom.get('lede', '')
            body, faqs = custom['body'], custom['faqs']
            lead = image_map().get((legacy or {}).get('image') or '')
            if lead:
                body = f'<figure><img src="{lead}" alt="{esc(name)} by Sky Clean Air" loading="eager"></figure>\n' + body
            title = custom.get('title') or seo_title(legacy, name)
            desc = custom.get('description') or (legacy or {}).get('description', '')
        elif legacy:
            h1 = f'{esc(name)} in <span class="hl">San Diego &amp; Orange County</span>'
            lede = esc(legacy['description'].replace('{{phone}}', ch.phone))
            body, faqs = strip_self_links(local_images(legacy['body']), path), legacy['faqs']
            title, desc = seo_title(legacy, name), legacy['description']
        else:
            h1 = esc(name)
            lede = esc(svc.get('blurb', cat['blurb']))
            body, faqs = f'<p>{esc(cat["blurb"])}</p>', []
            title, desc = f'{name} | Sky Clean Air', cat['blurb']

        crumbs = [('Home', '/'), ('Services', '/services/'), (cat['name'], f'/services/{cat["slug"]}/'), (name, None)]
        faq_html, faq_schema = faq_section(faqs, f'{name}: Frequently Asked Questions')

        # Where this service is offered: legacy neighborhood pages + live cities in newer regions
        locs = locations_for(slug)
        chips = ''.join(f'<a class="city-chip light" href="{p}">{esc(area_name(D, a))}</a>' for a, p in locs)
        oc = ''.join(f'<a class="city-chip light" href="/service-areas/{c["slug"]}/">{esc(c["name"])}</a>'
                     for c in D.cities('orange-county'))
        sd_block = f'<h3>San Diego County</h3><div class="city-cloud">{chips}</div>' if chips else ''
        area_html = f'''<section class="service-areas-block">
  <h2>Where We Offer {esc(name)}</h2>
  <p>Our crews provide {esc(name.lower())} across {" and ".join(regions)}. Choose your area for local details.</p>
  <h3>Orange County</h3><div class="city-cloud">{oc}</div>
  {sd_block}
  <p class="more-link"><a href="/service-areas/">View the full service area map &rarr;</a></p>
</section>'''

        siblings = [(s['name'], f'/{s["slug"]}/') for s in cat['services'] if s['slug'] != slug and not s.get('hidden')]
        side = sidebar(ch, D, f'More {cat["name"]} Services', siblings)
        service_schema = {
            '@context': 'https://schema.org', '@type': 'Service', 'serviceType': name,
            'provider': {'@type': 'HVACBusiness', 'name': D.site['name'], 'telephone': '+1-' + D.site['phone']},
            'areaServed': regions, 'url': D.site['domain'] + path,
        }
        img = image_map().get((legacy or {}).get('image') or '')
        site.add({
            'path': path, 'legacy': True, 'lastmod': (legacy or {}).get('modified'),
            'title': title, 'description': desc or cat['blurb'],
            'og_image': img or '/assets/images/story-team.jpg',
            'schema': [service_schema, breadcrumb_schema(D.site['domain'], crumbs)] + faq_schema,
            'body': page_hero(ch, h1, lede, crumbs, kicker=esc(cat['name'])) +
                    article_layout(f'<div class="prose">{body}</div>{faq_html}{area_html}', side) +
                    f'<section class="section bg-soft"><div class="container"><div class="section-head center"><h2>What Our <span class="grad-text">Customers</span> Say</h2></div>{components.reviews(ch, D, "2")}</div></section>' +
                    cta_band(ch),
        })


def service_card(D, svc, legacy):
    desc = (legacy or {}).get('description') or ''
    desc = re.sub(r'\s*Call (today|now).*$', '', desc.replace('{{phone}}', D.site['phone'])).strip()
    if len(desc) > 150:
        desc = desc[:150].rsplit(' ', 1)[0] + '…'
    return f'''<div class="mini-card">
  <h3><a class="card-link" href="/{svc["slug"]}/">{esc(svc["name"])}</a></h3>
  <p>{esc(desc)}</p>
  <span class="service-link" aria-hidden="true">Learn more &rarr;</span>
</div>'''


def category_hubs(site):
    D, ch = site.D, site.ch
    for cat in D.categories:
        path = f'/services/{cat["slug"]}/'
        custom = custom_copy('_' + cat['slug'])
        crumbs = [('Home', '/'), ('Services', '/services/'), (cat['name'], None)]
        svcs = [s for s in cat['services'] if not s.get('hidden')]
        cards = ''.join(service_card(D, s, legacy_by_path(f'/{s["slug"]}/')) for s in svcs)
        intro = custom['body'] if custom else f'<p class="lede-dark">{esc(cat["blurb"])}</p>'
        faq_html, faq_schema = faq_section(custom['faqs'], f'{cat["name"]} FAQs') if custom else ('', [])
        h1 = (custom or {}).get('h1') or f'{esc(cat["name"])} <span class="hl">Services</span>'
        lede = (custom or {}).get('lede') or esc(cat['blurb'])
        site.add({
            'path': path,
            'title': (custom or {}).get('title') or f'{cat["name"]} Services in San Diego & Orange County | Sky Clean Air',
            'description': (custom or {}).get('description') or cat['blurb'],
            'schema': [breadcrumb_schema(D.site['domain'], crumbs)] + faq_schema,
            'body': page_hero(ch, h1, lede, crumbs, kicker=f'{len(svcs)} services') +
                    f'''<section class="section"><div class="container">
  <div class="hub-intro prose">{intro}</div>
  <div class="mini-grid">{cards}</div>
  {faq_html}
</div></section>''' +
                    f'<section class="section bg-soft"><div class="container"><div class="section-head center"><h2>Explore <span class="grad-text">Other Services</span></h2></div>{components.services_grid(ch, D)}</div></section>' +
                    cta_band(ch),
        })


def services_index(site):
    D, ch = site.D, site.ch
    groups = []
    for cat in D.categories:
        svcs = [s for s in cat['services'] if not s.get('hidden')]
        links = ''.join(f'<li><a href="/{s["slug"]}/">{esc(s["name"])}</a></li>' for s in svcs)
        groups.append(f'''<div class="svc-group" id="{cat["slug"]}">
  <h2><span class="mega-icon">{icon(cat["icon"], 18)}</span><a href="/services/{cat["slug"]}/">{esc(cat["name"])}</a></h2>
  <p>{esc(cat["blurb"])}</p>
  <ul class="svc-list">{links}</ul>
</div>''')
    crumbs = [('Home', '/'), ('Services', None)]
    site.add({
        'path': '/services/',
        'title': 'HVAC, Air Duct, Dryer Vent & Attic Services | Sky Clean Air',
        'description': 'Every service Sky Clean Air offers: AC and heating, HVAC installs and repair, air duct and dryer vent cleaning, attic insulation, indoor air quality and commercial HVAC.',
        'schema': [breadcrumb_schema(D.site['domain'], crumbs)],
        'body': page_hero(ch, 'Every Service, <span class="hl">One Trusted Team</span>',
                          'From a same-day duct cleaning to a full system install — residential and commercial, across San Diego and Orange County.',
                          crumbs) +
                f'<section class="section"><div class="container">{components.services_grid(ch, D)}</div></section>' +
                f'<section class="section bg-soft"><div class="container"><div class="section-head center"><h2>The Full <span class="grad-text">Service List</span></h2></div><div class="svc-groups">{"".join(groups)}</div></div></section>' +
                cta_band(ch),
    })
