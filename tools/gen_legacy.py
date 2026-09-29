"""Generators for content migrated from the legacy WordPress site.

Input: content/legacy/{pages,posts}/<id>.json (from tools/parse_legacy.py)
and content/legacy/image-map.json (from tools/fetch_legacy_images.py).

Every legacy URL keeps its path. Page types:
  service-location   /ac-repair/clairemont/     -> service_location_page()
  post               /<slug>/                   -> post_page(), plus /blog/ index
  page               misc (privacy, terms, ...) -> misc_page()
Service pages (/ac-repair/) and area pages are built by gen_services.py /
gen_areas.py, which read legacy copy through `legacy_by_path()`.
"""
import glob
import html
import json
import os
import re
from functools import lru_cache

from sitelib import ROOT, breadcrumb_schema, cta_band, esc, icon, page_hero

LEGACY = os.path.join(ROOT, 'content', 'legacy')

# Legacy pages that are replaced by hand-built/new pages, drafts, or dead
# duplicates. Values are where the old URL should now point (a meta-refresh
# page is written for it), or None to drop it entirely.
RETIRED = {
    '/blog/': None, '/our-team/': None, '/about-us/': None, '/contact-us/': None, '/careers/': None,
    '/testimonials/': None, '/service-areas/': None, '/about-us/gallery/': None,
    '/homepage-hero-concept/': None,
    '/contact-us-nw/': '/contact-us/', '/landing-page-nw/': '/contact-us/',
    '/sky-clean-air-google-old/': '/', '/sky-clean-air-meta-old/': '/',
    '/shop/': '/specials/', '/project-map/': '/service-areas/', '/service-area-map/': '/service-areas/',
    '/attic-and-crawl-space/': '/services/attic-insulation/',
}
# Paid-ads landing / thank-you pages: migrated but kept out of search.
NOINDEX = {'/landing-page/', '/sky-clean-air-google/', '/sky-clean-air-meta/', '/thank-you/',
           '/thank-you-google/', '/thank-you-meta/'}


@lru_cache(maxsize=None)
def _load():
    recs = {}
    for kind in ('pages', 'posts'):
        for f in glob.glob(os.path.join(LEGACY, kind, '*.json')):
            r = json.load(open(f))
            if '-delete/' in r['path'] or r['path'].endswith('-delete'):
                continue
            recs[r['path']] = r
    return recs


@lru_cache(maxsize=None)
def image_map():
    p = os.path.join(LEGACY, 'image-map.json')
    return json.load(open(p)) if os.path.exists(p) else {}


def legacy_by_path(path):
    return _load().get(path)


def legacy_all(kind=None, typ=None):
    return [r for r in _load().values() if (kind is None or r['kind'] == kind) and (typ is None or r['type'] == typ)]


def local_images(body):
    """Point <img> at the migrated WebP copies; drop images we don't have."""
    m = image_map()

    def fig(mo):
        src = mo.group(1)
        return mo.group(0).replace(src, m[src]) if src in m else ''
    body = re.sub(r'<figure><img src="([^"]+)"[^>]*></figure>', fig, body)
    return re.sub(r'<img src="([^"]+)"[^>]*>', fig, body)


def strip_self_links(body, path):
    return re.sub(r'<a href="%s">(.*?)</a>' % re.escape(path), r'\1', body)


def text_excerpt(body, n=170):
    t = html.unescape(re.sub(r'<[^>]+>', ' ', body))
    t = re.sub(r'\s+', ' ', t).replace('{{phone}}', '').strip()
    return (t[:n].rsplit(' ', 1)[0] + '…') if len(t) > n else t


def faq_section(faqs, title='Frequently Asked Questions'):
    if not faqs:
        return '', []
    items = ''.join(
        f'<details class="faq-item"><summary>{esc(q)}{icon("chev", 20)}</summary><div class="faq-a">{a}</div></details>'
        for q, a in faqs)
    schema = {
        '@context': 'https://schema.org', '@type': 'FAQPage',
        'mainEntity': [{'@type': 'Question', 'name': q,
                        'acceptedAnswer': {'@type': 'Answer', 'text': re.sub(r'<[^>]+>', '', a).replace('{{phone}}', '')}}
                       for q, a in faqs],
    }
    return f'<section class="faq" id="faq"><h2>{title}</h2><div class="faq-list">{items}</div></section>', [schema]


def sidebar(ch, D, links_title=None, links=None, extra=''):
    """Sticky sidebar: quote card, optional related-links list, current specials."""
    options = ''.join(f'<option>{esc(c["name"])}</option>' for c in D.categories) + '<option>Other</option>'
    links_html = ''
    if links:
        items = ''.join(f'<li><a href="{h}">{esc(n)}</a></li>' for n, h in links)
        links_html = f'<div class="side-card"><h3>{esc(links_title)}</h3><ul class="side-links">{items}</ul></div>'
    specials = ''.join(
        f'<li><span class="sp-price">{esc(o["price"])}</span><span>{esc(o["title"])}</span></li>'
        for o in D.site['specials'] if o.get('active'))
    return f'''<aside class="content-side">
  <div class="side-card side-quote">
    <h3>Get a Free Estimate</h3>
    <p>Same-day and next-day appointments. Tell us what's going on and we'll call you back.</p>
    <a href="{ch.tel}" class="btn btn-primary btn-block">{icon("phone", 18)} {ch.phone}</a>
    <form class="quote-form side-form" data-quote-form>
      <label class="sr-only" for="side-name">Name</label><input id="side-name" name="name" placeholder="Your name" required>
      <label class="sr-only" for="side-phone">Phone</label><input id="side-phone" name="phone" type="tel" placeholder="Phone number" required>
      <label class="sr-only" for="side-service">Service</label><select id="side-service" name="service" required><option value="" disabled selected>Service needed</option>{options}</select>
      <button type="submit" class="btn btn-secondary btn-block">Request a Callback</button>
      <div class="form-success">Thanks! We'll call you back shortly.</div>
    </form>
  </div>
  {links_html}
  <div class="side-card side-specials"><h3>Current Specials</h3><ul>{specials}</ul><a href="/specials/">See all specials &rarr;</a></div>
  {extra}
</aside>'''


def article_layout(main_html, side_html):
    return f'''<section class="section content-section">
  <div class="container content-layout">
    <div class="content-main">{main_html}</div>
    {side_html}
  </div>
</section>'''


def seo_title(r, fallback):
    t = (r or {}).get('seo_title') or ''
    t = re.sub(r'\s*[|–-]\s*Sky Clean Air\s*$', '', t).strip()
    return f'{t or fallback} | Sky Clean Air'


# ---------------------------------------------------------------------------
# Service × neighborhood pages  (/ac-repair/clairemont/)
# ---------------------------------------------------------------------------
def area_name(D, slug, fallback=None):
    c = next((c for c in D.cities() if c['slug'] == slug), None)
    if c:
        return c['name']
    return fallback or slug.replace('-', ' ').title()


def service_locations(site):
    D, ch = site.D, site.ch
    recs = legacy_all('page', 'service-location')
    by_area = {}
    for r in recs:
        svc_slug, area_slug = r['path'].strip('/').split('/')
        by_area.setdefault(area_slug, []).append(svc_slug)
    for r in recs:
        svc_slug, area_slug = r['path'].strip('/').split('/')
        cat, svc = D.service(svc_slug)
        svc_name = svc['name'] if svc else r['title'].split(' in ')[0]
        name = area_name(D, area_slug, re.sub(r'^.* in ', '', r['h1'] or r['title']).replace(', CA', ''))
        h1 = f'{svc_name} in <span class="hl">{esc(name)}, CA</span>'
        crumbs = [('Home', '/'), ('Services', '/services/')]
        if cat:
            crumbs.append((cat['name'], f'/services/{cat["slug"]}/'))
        crumbs += [(svc_name, f'/{svc_slug}/'), (name, None)]
        body = strip_self_links(local_images(r['body']), r['path'])
        faq_html, faq_schema = faq_section(r['faqs'], f'{svc_name} in {name}: FAQs')
        others = [(D.service(s)[1]['name'] if D.service(s)[1] else s.replace('-', ' ').title(), f'/{s}/{area_slug}/')
                  for s in sorted(by_area[area_slug]) if s != svc_slug]
        area_link = [(f'All services in {name}', f'/service-areas/{area_slug}/')]
        side = sidebar(ch, D, f'More Services in {name}', area_link + others)
        lede = esc(r['description'].replace('{{phone}}', ch.phone)) if r['description'] else ''
        site.add({
            'path': r['path'], 'legacy': True, 'lastmod': r['modified'],
            'title': seo_title(r, f'{svc_name} in {name}, CA'),
            'description': r['description'] or f'{svc_name} in {name}, CA from Sky Clean Air.',
            'og_image': (image_map().get(r['image']) if r.get('image') else None) or '/assets/images/story-team.jpg',
            'schema': [breadcrumb_schema(D.site['domain'], crumbs)] + faq_schema,
            'body': page_hero(ch, h1, lede, crumbs, kicker=f'Serving {esc(name)} &amp; nearby') +
                    article_layout(f'<div class="prose">{body}</div>{faq_html}', side) + cta_band(ch),
        })


# ---------------------------------------------------------------------------
# Blog posts + index
# ---------------------------------------------------------------------------
POSTS_PER_PAGE = 24


def posts(site):
    D, ch = site.D, site.ch
    recs = sorted(legacy_all('post'), key=lambda r: r['date'], reverse=True)
    by_cat = {}
    for r in recs:
        for c in r.get('categories', []):
            by_cat.setdefault(c, []).append(r)
    for r in recs:
        if site.has(r['path']):
            print(f'  ! post {r["path"]} collides with an existing page; skipped')
            continue
        img = image_map().get(r['image']) if r.get('image') else None
        body = local_images(r['body'])
        if img:
            body = re.sub(r'^<figure>.*?</figure>\n?', '', body)  # drop a duplicate lead image
        crumbs = [('Home', '/'), ('Blog', '/blog/'), (r['title'], None)]
        faq_schema = []
        if r['faqs']:
            _, faq_schema = faq_section(r['faqs'])
        related = []
        for c in r.get('categories', []):
            for o in by_cat.get(c, []):
                if o is not r and o not in related:
                    related.append(o)
        related = related[:3] or [o for o in recs[:4] if o is not r][:3]
        date_str = format_date(r['date'])
        cats = ', '.join(r.get('categories', [])[:2])
        meta = f'<p class="post-meta">{icon("clock", 16)} {date_str}{" · " + esc(cats) if cats else ""}</p>'
        lead = f'<figure class="post-lead"><img src="{img}" alt="{esc(r["title"])}"></figure>' if img else ''
        rel_html = ''
        if related:
            rel_html = '<section class="related-posts"><h2>Keep Reading</h2><div class="blog-grid">' + \
                       ''.join(post_card(o) for o in related) + '</div></section>'
        article_schema = {
            '@context': 'https://schema.org', '@type': 'BlogPosting', 'headline': r['title'],
            'datePublished': r['date'], 'dateModified': r['modified'],
            'author': {'@type': 'Organization', 'name': D.site['name']},
            'publisher': {'@type': 'Organization', 'name': D.site['name']},
            **({'image': D.site['domain'] + img} if img else {}),
        }
        site.add({
            'path': r['path'], 'legacy': True, 'lastmod': r['modified'],
            'title': seo_title(r, r['title']),
            'description': r['description'] or text_excerpt(r['body'], 155),
            'og_image': img or '/assets/images/story-team.jpg',
            'body_class': 'page-post',
            'schema': [article_schema, breadcrumb_schema(D.site['domain'], crumbs)] + faq_schema,
            'body': page_hero(ch, esc(r['title']), '', crumbs, ctas=False, extra=meta) +
                    article_layout(f'{lead}<article class="prose">{body}</article>{rel_html}', sidebar(ch, D)) +
                    cta_band(ch),
        })
    blog_index(site, [r for r in recs if site.pages.get(r['path'], {}).get('legacy')])


def format_date(d):
    import datetime
    return datetime.date.fromisoformat(d).strftime('%B %-d, %Y')


def post_card(r):
    img = image_map().get(r['image']) if r.get('image') else None
    img_html = (f'<div class="post-card-img"><img src="{img}" alt="" loading="lazy"></div>' if img
                else '<div class="post-card-img post-card-noimg" aria-hidden="true"></div>')
    return f'''<article class="post-card">
  {img_html}
  <div class="post-card-body">
    <p class="post-card-date">{format_date(r["date"])}</p>
    <h3><a class="card-link" href="{r["path"]}">{esc(r["title"])}</a></h3>
    <p>{esc(text_excerpt(r["body"], 130))}</p>
  </div>
</article>'''


def blog_index(site, recs):
    ch = site.ch
    pages = [recs[i:i + POSTS_PER_PAGE] for i in range(0, len(recs), POSTS_PER_PAGE)]
    for n, chunk in enumerate(pages, 1):
        path = '/blog/' if n == 1 else f'/blog/page/{n}/'
        nav = pagination(n, len(pages))
        crumbs = [('Home', '/'), ('Blog', '/blog/' if n > 1 else None)] + ([(f'Page {n}', None)] if n > 1 else [])
        site.add({
            'path': path,
            'title': 'HVAC & Air Quality Tips Blog | Sky Clean Air' + (f' — Page {n}' if n > 1 else ''),
            'description': 'Practical HVAC, air duct, dryer vent, attic and indoor air quality advice from the Sky Clean Air team in San Diego and Orange County.',
            'noindex': n > 1,
            'body': page_hero(ch, 'HVAC &amp; Air Quality <span class="hl">Tips</span>',
                              'Practical advice from our technicians on keeping your home comfortable, efficient and breathing clean — '
                              f'{len(recs):,} articles and counting.', crumbs, ctas=False) +
                    f'<section class="section"><div class="container"><div class="blog-grid">{"".join(post_card(r) for r in chunk)}</div>{nav}</div></section>' +
                    cta_band(ch),
        })


def pagination(n, total):
    def href(i):
        return '/blog/' if i == 1 else f'/blog/page/{i}/'
    nums = sorted({1, 2, total - 1, total, n - 2, n - 1, n, n + 1, n + 2} & set(range(1, total + 1)))
    parts, prev = [], 0
    for i in nums:
        if i - prev > 1:
            parts.append('<span class="gap">…</span>')
        parts.append(f'<span class="current">{i}</span>' if i == n else f'<a href="{href(i)}">{i}</a>')
        prev = i
    prev_l = f'<a class="pg-prev" href="{href(n - 1)}">&larr; Newer</a>' if n > 1 else ''
    next_l = f'<a class="pg-next" href="{href(n + 1)}">Older &rarr;</a>' if n < total else ''
    return f'<nav class="pagination" aria-label="Blog pages">{prev_l}{"".join(parts)}{next_l}</nav>'


# ---------------------------------------------------------------------------
# Misc pages and redirects
# ---------------------------------------------------------------------------
def misc_pages(site):
    D, ch = site.D, site.ch
    service_slugs = {s['slug'] for _, s in D.all_services()}
    for r in legacy_all('page', 'page'):
        path = r['path']
        if path in RETIRED or path.strip('/') in service_slugs or site.has(path):
            continue
        if not re.sub(r'<[^>]+>', '', r['body']).strip():
            continue
        title = r['h1'] or r['title']
        crumbs = [('Home', '/')] + ([('HVAC & Air Cleaning', '/hvac-air-cleaning/')] if path.startswith('/hvac-air-cleaning/') and path != '/hvac-air-cleaning/' else []) + [(r['title'], None)]
        site.add({
            'path': path, 'legacy': True, 'lastmod': r['modified'], 'noindex': path in NOINDEX,
            'title': seo_title(r, title),
            'description': r['description'] or text_excerpt(r['body'], 155),
            'body': page_hero(ch, esc(title), '', crumbs) +
                    article_layout(f'<div class="prose">{local_images(r["body"])}</div>', sidebar(ch, D)) + cta_band(ch),
        })


def redirects(site):
    for old, new in RETIRED.items():
        if new and not site.has(old):
            site.add({
                'path': old, 'raw': True,
                'body': f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Moved</title>
<link rel="canonical" href="{site.D.site["domain"]}{new}"><meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url={new}"></head>
<body><p>This page has moved to <a href="{new}">{new}</a>.</p></body></html>''',
                'noindex': True,
            })


def fix_legacy_links(site):
    """Unwrap links in migrated content that point at pages that don't exist on the new site."""
    known = set(site.pages)

    def ok(href):
        if not href.startswith('/') or href.startswith('//'):
            return True
        p = href.split('#')[0].split('?')[0]
        if not p.endswith('/') and '.' not in p.rsplit('/', 1)[-1]:
            p += '/'
        return p in known or os.path.exists(os.path.join(ROOT, 'public', p.lstrip('/')))

    def sub(m):
        return m.group(0) if ok(m.group(1)) else m.group(2)
    for p in site.pages.values():
        if p.get('legacy'):
            p['body'] = re.sub(r'<a href="(/[^"]*)">(.*?)</a>', sub, p['body'])
