"""Shared templates for the Sky Clean Air site builder.

Everything that appears on more than one page lives here: the <head>, top
bar, header + nav, mobile drawer, footer, and the reusable content blocks
("components") that hand-written pages pull in with {{component:name}}.

Data comes from src/data/*.json (loaded once into `D` by build.py).
"""
import hashlib
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC = os.path.join(ROOT, 'public')
DATA_DIR = os.path.join(ROOT, 'src', 'data')

esc = html.escape


def load_json(name):
    with open(os.path.join(DATA_DIR, name)) as f:
        return json.load(f)


class Data:
    """All site data, loaded once."""

    def __init__(self):
        self.site = load_json('site.json')
        self.services = load_json('services.json')
        self.areas = load_json('areas.json')
        self.team = load_json('team.json')
        self.reviews = load_json('reviews.json')

    # --- services ---
    @property
    def categories(self):
        return self.services['categories']

    def category(self, slug):
        return next(c for c in self.categories if c['slug'] == slug)

    def all_services(self):
        for c in self.categories:
            for s in c['services']:
                yield c, s

    def service(self, slug):
        return next(((c, s) for c, s in self.all_services() if s['slug'] == slug), (None, None))

    # --- areas ---
    @property
    def regions(self):
        return sorted(self.areas['regions'], key=lambda r: r['order'])

    def region(self, slug):
        return next(r for r in self.areas['regions'] if r['slug'] == slug)

    def cities(self, region_slug=None):
        cs = self.areas['cities']
        if region_slug:
            cs = [c for c in cs if c['region'] == region_slug]
        return cs


def asset_version(rel):
    """Short content hash for cache-busting ?v= query strings."""
    try:
        with open(os.path.join(PUBLIC, rel.lstrip('/')), 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()[:8]
    except FileNotFoundError:
        return '0'


# ---------------------------------------------------------------------------
# Icons (stroke icons, 24x24 viewBox)
# ---------------------------------------------------------------------------
ICONS = {
    'phone': '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>',
    'thermo': '<path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0z"/>',
    'wind': '<path d="M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2"/>',
    'fire': '<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>',
    'flame': '<path d="M12 22c4 0 7-2.7 7-6.5 0-3-2-5.5-4-7.5-.5 2-1.5 3-3 3.5.5-3-1-6-4-8.5 0 4-4 6.5-4 11 0 4.4 3.6 8 8 8z"/>',
    'home': '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>',
    'drop': '<path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/>',
    'snow': '<line x1="12" y1="2" x2="12" y2="22"/><line x1="4.93" y1="7" x2="19.07" y2="17"/><line x1="4.93" y1="17" x2="19.07" y2="7"/><polyline points="9 4 12 7 15 4"/><polyline points="9 20 12 17 15 20"/>',
    'building': '<rect x="4" y="2" width="16" height="20" rx="2"/><line x1="9" y1="6" x2="9" y2="6.01"/><line x1="15" y1="6" x2="15" y2="6.01"/><line x1="9" y1="10" x2="9" y2="10.01"/><line x1="15" y1="10" x2="15" y2="10.01"/><line x1="9" y1="14" x2="9" y2="14.01"/><line x1="15" y1="14" x2="15" y2="14.01"/><path d="M10 22v-4h4v4"/>',
    'pin': '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>',
    'check': '<polyline points="20 6 9 17 4 12"/>',
    'chev': '<polyline points="6 9 12 15 18 9"/>',
    'arrow': '<line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>',
    'menu': '<line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>',
    'close': '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
    'clock': '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    'shield': '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/>',
    'star': '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
    'user': '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    'truck': '<rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/>',
    'search': '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
}


def badge_html(text, cls='menu-badge'):
    return f' <span class="{cls}">{esc(text)}</span>' if text else ''


def icon(name, size=24, cls=''):
    c = f' class="{cls}"' if cls else ''
    return (f'<svg{c} width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>')


SOCIAL_ICONS = {
    'Instagram': '<rect x="2" y="2" width="20" height="20" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none"/>',
    'Facebook': '<path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/>',
    'TikTok': '<path d="M9 12a4 4 0 1 0 4 4V4a5 5 0 0 0 5 5"/>',
    'Yelp': '<path d="M12 2l2.6 5.9 6.4.6-4.9 4.2 1.5 6.3L12 15.9 6.4 19l1.5-6.3-4.9-4.2 6.4-.6z"/>',
}


# ---------------------------------------------------------------------------
# Page chrome
# ---------------------------------------------------------------------------
class Chrome:
    def __init__(self, D):
        self.D = D
        self.s = D.site

    # -- small helpers --
    @property
    def phone(self):
        return self.s['phone']

    @property
    def tel(self):
        return 'tel:' + self.s['phone_tel']

    def call_btn(self, label=None, cls='btn btn-primary'):
        return f'<a href="{self.tel}" class="{cls}">{esc(label or "Call Now — " + self.phone)}</a>'

    # -- head --
    def head(self, p):
        s = self.s
        title = p['title']
        desc = p.get('description', '')
        canonical = s['domain'] + p['path']
        robots = '<meta name="robots" content="noindex, follow">\n' if p.get('noindex') else ''
        extra = p.get('head_extra', '')
        css_v = asset_version('css/styles.css')
        return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(canonical)}">
{robots}<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(s['name'])}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{s['domain']}{p.get('og_image', '/assets/images/story-team.jpg')}">
<link rel="icon" href="{s['logo']}">
<link rel="preload" href="/assets/fonts/antonio/Antonio-Bold.ttf" as="font" type="font/ttf" crossorigin>
<link rel="stylesheet" href="/css/styles.css?v={css_v}">
{extra}{self.schema(p)}
</head>'''

    def schema(self, p):
        """LocalBusiness JSON-LD on every page (plus page-specific extras)."""
        s = self.s
        a = s['address']
        biz = {
            '@context': 'https://schema.org',
            '@type': 'HVACBusiness',
            'name': s['name'],
            'url': s['domain'] + '/',
            'telephone': '+1-' + s['phone'],
            'image': s['domain'] + s['logo'],
            'foundingDate': str(s['founded']),
            'address': {'@type': 'PostalAddress', 'streetAddress': a['street'], 'addressLocality': a['city'],
                        'addressRegion': a['state'], 'postalCode': a['zip'], 'addressCountry': 'US'},
            'geo': {'@type': 'GeoCoordinates', 'latitude': a['lat'], 'longitude': a['lng']},
            'openingHours': ['Mo-Fr 08:00-18:00', 'Sa 08:00-15:00'],
            'areaServed': [r['name'] for r in self.D.regions if r['status'] != 'coming-soon'],
            'sameAs': [x['url'] for x in s['socials']],
        }
        out = [biz] + p.get('schema', [])
        return '\n'.join(f'<script type="application/ld+json">{json.dumps(o, ensure_ascii=False)}</script>' for o in out)

    # -- nav model (single source for desktop mega-menu, mobile drawer and footer) --
    def nav(self):
        D = self.D
        services_cols = []
        for c in D.categories:
            items = [s for s in c['services'] if not s.get('hidden')]
            services_cols.append({
                'label': c['name'], 'href': f'/services/{c["slug"]}/', 'icon': c['icon'],
                'items': [(s['name'], f'/{s["slug"]}/') for s in items[:6]],
                'more': len(items) > 6,
            })
        areas = []
        for r in D.regions:
            areas.append((r['name'], f'/service-areas/{r["slug"]}/', r.get('badge', '')))
        return [
            {'label': 'Services', 'href': '/services/', 'mega': services_cols},
            {'label': 'Service Areas', 'href': '/service-areas/',
             'items': areas + [('Service Area Map', '/service-areas/#map', '')]},
            {'label': 'About', 'href': '/about-us/',
             'items': [('Our Story', '/about-us/', ''), ('Our Team', '/our-team/', ''),
                       ('Reviews', '/testimonials/', ''), ('Careers', '/careers/', ''),
                       ('Gallery', '/about-us/gallery/', '')]},
            {'label': 'Specials', 'href': '/specials/'},
            {'label': 'Blog', 'href': '/blog/'},
            {'label': 'Contact', 'href': '/contact-us/'},
        ]

    def _active(self, p, href):
        path = p['path']
        if href == '/':
            return path == '/'
        return path.startswith(href.split('#')[0])

    def header(self, p):
        s = self.s
        socials = ''.join(f'<a href="{x["url"]}" target="_blank" rel="noopener">{x["name"]}</a>' for x in s['socials'])
        a = s['address']
        nav_html = []
        for item in self.nav():
            active = ' active' if self._active(p, item['href']) else ''
            if 'mega' in item:
                cols = ''.join(
                    f'<div class="mega-col"><a class="mega-head" href="{c["href"]}">'
                    f'<span class="mega-icon">{icon(c["icon"], 18)}</span>{esc(c["label"])}</a><ul>'
                    + ''.join(f'<li><a href="{h}">{esc(n)}</a></li>' for n, h in c['items'])
                    + (f'<li><a class="mega-more" href="{c["href"]}">View all &rarr;</a></li>' if c['more'] else '')
                    + '</ul></div>' for c in item['mega'])
                nav_html.append(
                    f'<div class="nav-item has-menu"><a href="{item["href"]}" class="nav-link{active}">{item["label"]}{icon("chev", 14, "nav-chev")}</a>'
                    f'<div class="nav-menu mega"><div class="mega-grid">{cols}</div>'
                    f'<div class="mega-foot"><a href="/services/">See every service we offer &rarr;</a>'
                    f'<a href="{self.tel}">Not sure what you need? Call {self.phone}</a></div></div></div>')
            elif 'items' in item:
                links = ''.join(
                    f'<a href="{h}">{esc(n)}{badge_html(b)}</a>' for n, h, b in item['items'])
                nav_html.append(
                    f'<div class="nav-item has-menu"><a href="{item["href"]}" class="nav-link{active}">{item["label"]}{icon("chev", 14, "nav-chev")}</a>'
                    f'<div class="nav-menu">{links}</div></div>')
            else:
                nav_html.append(f'<div class="nav-item"><a href="{item["href"]}" class="nav-link{active}">{item["label"]}</a></div>')

        mobile = []
        for item in self.nav():
            if 'mega' in item:
                sub = ''.join(f'<a href="{c["href"]}">{esc(c["label"])}</a>' for c in item['mega'])
                sub += '<a href="/services/">All Services</a>'
            elif 'items' in item:
                sub = ''.join(f'<a href="{h}">{esc(n)}</a>' for n, h, _ in item['items'])
            else:
                mobile.append(f'<a class="m-link" href="{item["href"]}">{item["label"]}</a>')
                continue
            mobile.append(f'<details class="m-group"><summary>{item["label"]}{icon("chev", 18)}</summary><div class="m-sub">{sub}</div></details>')

        return f'''<div class="scroll-progress" id="scroll-progress"></div>

<div class="top-bar">
  <div class="container">
    <div class="top-bar-left">
      <span>Contractor License #{s["license"]}</span>
      <a href="/contact-us/">{esc(a["street"])}, {a["city"]}, {a["state"]} {a["zip"]}</a>
    </div>
    <div class="top-bar-social">{socials}</div>
  </div>
</div>

<header class="site-header" id="top">
  <div class="container">
    <a href="/" class="brand" aria-label="{esc(s["name"])} home">
      <img src="{s["logo"]}" alt="{esc(s["name"])} logo" width="600" height="316">
    </a>
    <nav class="main-nav" aria-label="Primary">{"".join(nav_html)}</nav>
    <div class="header-actions">
      <a href="/contact-us/#quote" class="btn btn-secondary btn-quote">Get a Quote</a>
      <a href="{self.tel}" class="btn-call">{icon("phone", 20)}<span>{self.phone}</span></a>
    </div>
    <button class="nav-toggle" aria-label="Open menu">{icon("menu", 24)}</button>
  </div>
</header>

<div class="mobile-nav" aria-hidden="true">
  <div class="mobile-nav-top">
    <a href="/"><img src="{s["logo"]}" alt="{esc(s["name"])} logo"></a>
    <button class="mobile-nav-close" aria-label="Close menu">{icon("close", 24)}</button>
  </div>
  <nav class="mobile-nav-links" aria-label="Mobile"><a class="m-link" href="/">Home</a>{"".join(mobile)}</nav>
  <div class="mobile-nav-cta">
    <a href="{self.tel}" class="btn btn-primary btn-block">Call {self.phone}</a>
    <a href="/contact-us/#quote" class="btn btn-secondary btn-block">Get a Quote</a>
  </div>
</div>

<div class="mobile-call-bar">
  <a href="{self.tel}">{icon("phone", 18)} Call Now — {self.phone}</a>
</div>'''

    def footer(self):
        s = self.s
        a = s['address']
        D = self.D
        socials = ''.join(
            f'<a href="{x["url"]}" target="_blank" rel="noopener" aria-label="{x["name"]}">'
            f'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{SOCIAL_ICONS[x["name"]]}</svg></a>'
            for x in s['socials'])
        svc = ''.join(f'<li><a href="/services/{c["slug"]}/">{esc(c["name"])}</a></li>' for c in D.categories)
        regions = ''.join(
            f'<li><a href="/service-areas/{r["slug"]}/">{esc(r["name"])}</a>{badge_html(r.get("badge"), "footer-badge")}</li>'
            for r in D.regions)
        hours = ''.join(f'<li>{d} · {h}</li>' for d, h in s['hours'] if h != 'Closed')
        options = ''.join(f'<option>{esc(c["name"])}</option>' for c in D.categories) + '<option>Other</option>'
        return f'''<footer class="site-footer" id="contact">
  <div class="footer-top">
    <div class="container footer-grid">
      <div class="footer-brand">
        <img src="{s["logo"]}" alt="{esc(s["name"])} logo">
        <p>Family-owned and operated, bringing cleaner air and dependable comfort to Southern California homes and businesses since {s["founded"]}.</p>
        <div class="footer-socials">{socials}</div>
      </div>

      <div class="footer-col">
        <h4>Services</h4>
        <ul>{svc}<li><a href="/services/">All Services</a></li></ul>
      </div>

      <div class="footer-col">
        <h4>Company</h4>
        <ul>
          <li><a href="/about-us/">About Us</a></li>
          <li><a href="/our-team/">Our Team</a></li>
          <li><a href="/testimonials/">Reviews</a></li>
          <li><a href="/specials/">Specials</a></li>
          <li><a href="/careers/">Careers</a></li>
          <li><a href="/blog/">Blog</a></li>
          <li><a href="/contact-us/">Contact</a></li>
        </ul>
        <h4 class="footer-sub">Service Areas</h4>
        <ul>{regions}</ul>
      </div>

      <div class="footer-col">
        <h4>Contact</h4>
        <ul>
          <li><a href="{self.tel}">{self.phone}</a></li>
          <li><address>{esc(a["street"])}<br>{a["city"]}, {a["state"]} {a["zip"]}</address></li>
          {hours}
          <li>Contractor License #{s["license"]}</li>
        </ul>
      </div>

      <div class="footer-col footer-form">
        <h4>Request Service</h4>
        <p class="form-lede">Tell us what's going on — we'll call you back the same day.</p>
        <form class="quote-form" data-quote-form>
          <div class="form-grid">
            <div class="field full"><label for="footer-name">Name</label><input type="text" id="footer-name" name="name" placeholder="Your name" required></div>
            <div class="field full"><label for="footer-phone">Phone</label><input type="tel" id="footer-phone" name="phone" placeholder="(619) 000-0000" required></div>
            <div class="field full"><label for="footer-service">Service Needed</label>
              <select id="footer-service" name="service" required><option value="" disabled selected>Select a service</option>{options}</select></div>
          </div>
          <button type="submit" class="btn btn-primary btn-block" style="margin-top:16px;">Request a Callback</button>
          <div class="form-success">Thanks! We'll call you back shortly.</div>
        </form>
      </div>
    </div>
  </div>

  <div class="footer-bottom">
    <div class="container">
      <p>&copy; {s.get("year", 2026)} {esc(s["name"])}. All rights reserved.</p>
      <p class="footer-legal-links"><a href="/privacy-policy/">Privacy Policy</a> · <a href="/terms-conditions/">Terms &amp; Conditions</a> · <a href="/sitemap.xml">Sitemap</a></p>
    </div>
  </div>
</footer>'''

    def page(self, p):
        body_class = ' '.join(['has-hero'] + p.get('body_class', '').split())
        js_v = asset_version('js/app.js')
        scripts = p.get('scripts', '')
        return f'''{self.head(p)}
<body class="{body_class}">

{self.header(p)}

<main>
{p["body"]}
</main>

{self.footer()}

<script src="/js/app.js?v={js_v}"></script>
{scripts}
</body>
</html>
'''


# ---------------------------------------------------------------------------
# Reusable page sections
# ---------------------------------------------------------------------------
def wave(fill='#ffffff', flip=False):
    d = 'M0,50 C420,-10 1020,100 1440,30 L1440,90 L0,90 Z' if flip else 'M0,40 C360,100 1080,-10 1440,50 L1440,90 L0,90 Z'
    return (f'<div class="wave-divider" aria-hidden="true"><svg viewBox="0 0 1440 90" preserveAspectRatio="none">'
            f'<path d="{d}" fill="{fill}"/></svg></div>')


def breadcrumbs(crumbs):
    """crumbs: [(label, href or None), ...] — rendered visibly and as JSON-LD."""
    parts = []
    for i, (label, href) in enumerate(crumbs):
        if href and i < len(crumbs) - 1:
            parts.append(f'<a href="{href}">{esc(label)}</a>')
        else:
            parts.append(f'<span aria-current="page">{esc(label)}</span>')
    return '<nav class="crumbs" aria-label="Breadcrumb">' + '<span class="sep">/</span>'.join(parts) + '</nav>'


def breadcrumb_schema(domain, crumbs):
    return {
        '@context': 'https://schema.org', '@type': 'BreadcrumbList',
        'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'name': label, **({'item': domain + href} if href else {})}
            for i, (label, href) in enumerate(crumbs)
        ],
    }


def page_hero(ch, title_html, lede='', crumbs=None, kicker='', ctas=True, media=None, extra=''):
    """Dark hero band used at the top of every inner page."""
    crumbs_html = breadcrumbs(crumbs) if crumbs else ''
    kicker_html = f'<span class="hero-badge"><span class="dot"></span> {kicker}</span>' if kicker else ''
    lede_html = f'<p class="lede">{lede}</p>' if lede else ''
    cta_html = ''
    if ctas:
        cta_html = (f'<div class="hero-ctas">{ch.call_btn()}'
                    f'<a href="/contact-us/#quote" class="btn btn-secondary">Get a Quote</a></div>')
    media_html = ''
    if media:
        media_html = f'<div class="hero-media"><img src="{media}" alt="" loading="eager"></div>'
    return f'''<section class="page-hero">
  {media_html}<div class="hero-overlay"></div>
  <div class="hero-grid" aria-hidden="true"></div>
  <div class="container">
    {crumbs_html}
    <div class="hero-content">
      {kicker_html}
      <h1>{title_html}</h1>
      {lede_html}
      {cta_html}
      {extra}
    </div>
  </div>
  {wave()}
</section>'''


def cta_band(ch, title='Ready For <span class="grad-text">Cleaner Air</span>?',
             text='Get a free estimate today — same-day and next-day appointments available.'):
    return f'''<section class="section-tight">
  <div class="container">
    <div class="cta-band" data-reveal>
      <div class="hero-grid" aria-hidden="true"></div>
      <div>
        <h2>{title}</h2>
        <p>{text}</p>
      </div>
      <div class="cta-actions">
        {ch.call_btn("Call " + ch.phone)}
        <a href="/contact-us/#quote" class="btn btn-outline">Get a Quote</a>
      </div>
    </div>
  </div>
</section>'''


def placeholder(ch, label, note='', cls=''):
    """Labeled box marking where a pending asset goes. Hidden when show_placeholders is false."""
    if not ch.s.get('show_placeholders'):
        return ''
    note_html = f'<span class="ph-note">{esc(note)}</span>' if note else ''
    return f'<div class="asset-placeholder {cls}"><span class="ph-label">{esc(label)}</span>{note_html}</div>'


def mascot(ch, pose='wave', cls=''):
    """Skylar the Home Service Eagle. Renders the artwork once it's in site.json, else a placeholder slot."""
    m = ch.s['mascot']
    src = m['images'].get(pose)
    if src:
        return (f'<figure class="mascot mascot-{pose} {cls}"><img src="{src}" '
                f'alt="{esc(m["name"])}, {esc(m["title"])}" loading="lazy"></figure>')
    return placeholder(ch, f'{m["name"]} — {m["title"]}', f'Mascot artwork slot ({pose.replace("_", " ")} pose)',
                       f'mascot-slot {cls}')


def stars(n=5):
    return '<div class="stars" aria-label="5 out of 5 stars">' + '★' * n + '</div>'


QUOTE_SVG = ('<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 7c-1.7 0-3 1.3-3 3v4c0 1.7 1.3 3 3 3h1v-3H7c-.6 0-1-.4-1-1v-1h2c1.1 0 2-.9 2-2v-1c0-1.1-.9-2-2-2H7zm10 0c-1.7 0-3 1.3-3 3v4c0 1.7 1.3 3 3 3h1v-3h-1c-.6 0-1-.4-1-1v-1h2c1.1 0 2-.9 2-2v-1c0-1.1-.9-2-2-2h-1z"/></svg>')


def testimonial_cards(reviews):
    return ''.join(f'''<div class="testimonial-card">
  <div class="quote-icon" aria-hidden="true">{QUOTE_SVG}</div>
  {stars()}
  <p>"{esc(r["text"])}"</p>
  <div class="testimonial-author"><strong>{esc(r["name"])}</strong><span>{esc(r.get("source", "Verified Customer"))}</span></div>
</div>''' for r in reviews)


def slugify(s):
    s = s.lower().replace('&', 'and')
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return s.strip('-')
