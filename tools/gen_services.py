"""The 8 service pages (/services/<category>/), the /services/ index, and
redirects from every retired individual-service URL.

One page per service category. Each page is built from:
  src/content/services/_<category>.html — hand-written copy (front matter:
      title, description, h1, lede; HTML body). A trailing
      <h2>Frequently Asked Questions</h2> of <h3>/<p> pairs becomes the
      FAQ accordion + FAQPage schema.
  src/data/services.json — the sub-services the page covers, listed in an
      "included" section (their old per-service URLs redirect here).
"""
import os
import re

import components
from gen_legacy import article_layout, faq_section, image_map, legacy_by_path, sidebar
from sitelib import ROOT, breadcrumb_schema, cta_band, esc, icon, page_hero

CONTENT = os.path.join(ROOT, 'src', 'content', 'services')


def category_url(cat):
    return f'/services/{cat["slug"]}/'


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


def included_section(cat):
    svcs = [s for s in cat['services'] if not s.get('hidden')]
    if cat['slug'] == 'commercial':
        groups = {}
        for s in svcs:
            groups.setdefault(s.get('group', 'Other'), []).append(s)
        cols = ''.join(
            f'<div class="inc-group"><h3>{esc(g)}</h3><ul>'
            + ''.join(f'<li>{esc(s["name"].replace("Commercial ", ""))}</li>' for s in items) + '</ul></div>'
            for g, items in groups.items())
        return f'''<section class="included" id="included">
  <h2>Commercial Services We Offer</h2>
  <div class="inc-groups">{cols}</div>
</section>'''
    items = ''.join(
        f'<div class="inc-item"><span class="inc-check">{icon("check", 16)}</span>'
        f'<div><h3>{esc(s["name"])}</h3><p>{esc(s.get("summary", ""))}</p></div></div>' for s in svcs)
    return f'''<section class="included" id="included">
  <h2>What's Included in Our {esc(cat["name"])} Service</h2>
  <div class="inc-grid">{items}</div>
</section>'''


def area_cta(D, name):
    regions = [r['name'] for r in D.regions if r['status'] != 'coming-soon']
    live = sum(1 for c in D.cities() if (c.get('status') or D.region(c['region'])['status']) != 'coming-soon')
    return f'''<section class="service-areas-cta">
  <span class="sac-icon">{icon("pin", 26)}</span>
  <div class="sac-copy">
    <h2>Where We Offer {esc(name)}</h2>
    <p>Our crews work in {live}+ communities across {" and ".join(regions)}.</p>
  </div>
  <a class="btn btn-primary" href="/service-areas/">View Our Service Areas &rarr;</a>
</section>'''


def lead_image(cat):
    """The legacy banner of the category's first sub-service that has one."""
    for s in cat['services']:
        img = image_map().get((legacy_by_path(f'/{s["slug"]}/') or {}).get('image') or '')
        if img:
            return img
    return None


def service_pages(site):
    D, ch = site.D, site.ch
    regions = [r['name'] for r in D.regions if r['status'] != 'coming-soon']
    for cat in D.categories:
        path = category_url(cat)
        custom = custom_copy('_' + cat['slug']) or {'body': f'<p>{esc(cat["blurb"])}</p>', 'faqs': []}
        name = cat['name']
        crumbs = [('Home', '/'), ('Services', '/services/'), (name, None)]
        h1 = custom.get('h1') or f'{esc(name)} in <span class="hl">San Diego &amp; Orange County</span>'
        lede = custom.get('lede') or esc(cat['blurb'])
        faq_html, faq_schema = faq_section(custom['faqs'], f'{name}: Frequently Asked Questions')
        lead = lead_image(cat)
        lead_html = f'<figure><img src="{lead}" alt="{esc(name)} services by Sky Clean Air" loading="eager"></figure>\n' if lead else ''
        others = [(c['name'], category_url(c)) for c in D.categories if c is not cat]
        service_schema = {
            '@context': 'https://schema.org', '@type': 'Service', 'serviceType': name,
            'provider': {'@type': 'HVACBusiness', 'name': D.site['name'], 'telephone': '+1-' + D.site['phone']},
            'areaServed': regions, 'url': D.site['domain'] + path,
            'hasOfferCatalog': {'@type': 'OfferCatalog', 'name': name, 'itemListElement': [
                {'@type': 'Offer', 'itemOffered': {'@type': 'Service', 'name': s['name']}}
                for s in cat['services'] if not s.get('hidden')]},
        }
        site.add({
            'path': path,
            'title': custom.get('title') or f'{name} in San Diego & Orange County | Sky Clean Air',
            'description': custom.get('description') or cat['blurb'],
            'og_image': lead or '/assets/images/story-team.jpg',
            'schema': [service_schema, breadcrumb_schema(D.site['domain'], crumbs)] + faq_schema,
            'body': page_hero(ch, h1, lede, crumbs, kicker=esc(name)) +
                    article_layout(f'<div class="prose">{lead_html}{custom["body"]}</div>{included_section(cat)}'
                                   f'{faq_html}{area_cta(D, name)}',
                                   sidebar(ch, D, 'Our Other Services', others)) +
                    f'<section class="section bg-soft"><div class="container"><div class="section-head center"><h2>What Our <span class="grad-text">Customers</span> Say</h2></div>{components.reviews(ch, D, "2")}</div></section>' +
                    cta_band(ch),
        })


def services_index(site):
    D, ch = site.D, site.ch
    crumbs = [('Home', '/'), ('Services', None)]
    site.add({
        'path': '/services/',
        'title': 'HVAC, Air Duct, Dryer Vent & Attic Services | Sky Clean Air',
        'description': 'Sky Clean Air services: air conditioning, HVAC systems, heating, air ducts, dryer vents, attic & insulation, indoor air quality and commercial — across San Diego and Orange County.',
        'schema': [breadcrumb_schema(D.site['domain'], crumbs)],
        'body': page_hero(ch, 'Every Service, <span class="hl">One Trusted Team</span>',
                          'From a same-day duct cleaning to a full system install — residential and commercial, across San Diego and Orange County.',
                          crumbs) +
                f'<section class="section"><div class="container">{components.services_grid(ch, D)}</div></section>' +
                cta_band(ch),
    })


def service_redirects(site):
    """Every retired individual-service URL → its category page."""
    for cat in site.D.categories:
        for s in cat['services']:
            site.redirect(f'/{s["slug"]}/', category_url(cat))
