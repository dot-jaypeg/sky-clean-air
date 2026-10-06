"""Components that hand-written pages can drop in with {{component:name[:arg]}}.

Each takes (ch, D, arg) — the Chrome, the site Data, and the optional
argument after the second colon — and returns HTML.
"""
from sitelib import cta_band, esc, icon, mascot as mascot_slot, placeholder, testimonial_cards, wave


def services_grid(ch, D, arg=None):
    """One card per service category. arg='residential' hides Commercial."""
    cats = [c for c in D.categories if not (arg == 'residential' and c['slug'] == 'commercial')]
    cards = []
    for i, c in enumerate(cats):
        delay = f' style="--reveal-delay:{(i % 4) * 0.08:.2f}s"' if i % 4 else ''
        top = [s for s in c['services'] if not s.get('hidden')][:3]
        links = ''.join(f'<li>{esc(s["name"])}</li>' for s in top)
        cards.append(f'''<div class="service-card" data-reveal{delay}>
  <div class="service-icon">{icon(c["icon"], 28)}</div>
  <h3><a class="card-link" href="/services/{c["slug"]}/">{esc(c["name"])}</a></h3>
  <p>{esc(c["blurb"])}</p>
  <ul class="service-card-list">{links}</ul>
  <span class="service-link" aria-hidden="true">Explore {esc(c["name"])} &rarr;</span>
</div>''')
    return f'<div class="services-grid">{"".join(cards)}</div>'


def stat_band(ch, D, arg=None):
    s = D.site
    from datetime import date
    years = date.today().year - s['founded']
    city_count = sum(1 for c in D.cities() if (c.get('status') or D.region(c['region'])['status']) != 'coming-soon')
    stats = [(years, '+', 'Years In Business'), (100, '%', 'Licensed &amp; Insured'),
             (5, '★', 'Google &amp; Yelp Rated'), (city_count, '+', 'Communities Served')]
    items = ''.join(
        f'<div class="counter-item"><div class="num" data-count="{n}"><span class="val">{n:,}</span><span class="suf">{suf}</span></div>'
        f'<div class="lbl">{lbl}</div></div>' for n, suf, lbl in stats)
    return f'''<section class="section stat-band bg-dark">
  <div class="hero-grid" aria-hidden="true"></div>
  <div class="container">
    <div class="section-head center" data-reveal style="margin-bottom:56px;">
      <h2>Built On Trust, Backed By <span class="grad-text">Results</span></h2>
    </div>
    <div class="counter-row" data-reveal>{items}</div>
  </div>
  {wave("#f2f7f9", flip=True)}
</section>'''


def reviews(ch, D, arg=None):
    """The review-aggregator widget if configured, otherwise our hand-picked testimonials."""
    widget = D.site['widgets'].get('reviews')
    if widget:
        return f'<div class="widget-embed reviews-widget" data-reveal>{widget}</div>'
    r = D.reviews
    limit = int(arg) if arg else len(r['items'])
    ph = placeholder(ch, 'All-platform reviews widget',
                     f'Trustindex / Contractor Commerce aggregator goes here — {r["summary"]["count_label"]} from '
                     + ', '.join(r['summary']['platforms']), 'ph-wide')
    return f'''{ph}<div class="testimonial-grid" data-reveal>{testimonial_cards(r["items"][:limit])}</div>'''


def contractor_commerce(ch, D, arg=None):
    widget = D.site['widgets'].get('contractor_commerce')
    if widget:
        return f'<div class="widget-embed cc-widget">{widget}</div>'
    return placeholder(ch, 'Contractor Commerce widget', 'Online booking / financing widget goes here once we have the embed code',
                       'ph-wide')


def region_status(D, city):
    return city.get('status') or D.region(city['region'])['status']


def areas_band(ch, D, arg=None):
    """Dark video band listing every region (in priority order) and its cities."""
    groups = []
    for r in D.regions:
        cities = D.cities(r['slug'])
        if r['slug'] == 'san-diego-county':
            cities = [c for c in cities if c['type'] == 'city'] + [c for c in cities if c.get('featured')]
        chips = []
        for c in cities:
            live = region_status(D, c) != 'coming-soon'
            tag = 'a' if live else 'span'
            href = f' href="/service-areas/{c["slug"]}/"' if live else ''
            chips.append(f'<{tag} class="city-chip{"" if live else " soon"}"{href}>{esc(c["name"])}</{tag}>')
        badge = f'<span class="region-badge">{esc(r["badge"])}</span>' if r.get('badge') else ''
        groups.append(f'''<div class="region-group region-{r["status"]}">
  <h3><a href="/service-areas/{r["slug"]}/">{esc(r["name"])}</a> {badge}</h3>
  <div class="city-cloud">{"".join(chips)}</div>
</div>''')
    return f'''<section class="area-band section" id="areas">
  <div class="area-media" aria-hidden="true">
    <video autoplay muted loop playsinline poster="/assets/images/area-bg-poster.jpg">
      <source src="/assets/video/area-bg.webm" type="video/webm">
      <source src="/assets/video/area-bg.mp4" type="video/mp4">
    </video>
  </div>
  <div class="area-overlay" aria-hidden="true"></div>
  <div class="container">
    <div class="area-head section-head" data-reveal>
      <h2>Serving <span class="grad-text">Southern California</span></h2>
      <p>Orange County and San Diego County — if you're within our reach, we're already on our way.</p>
    </div>
    <div class="region-groups" data-reveal>{"".join(groups)}</div>
    <p class="area-links"><a href="/service-areas/" class="btn btn-secondary">See the full service area map &rarr;</a></p>
  </div>
</section>'''


def specials(ch, D, arg=None):
    cards = ''.join(f'''<div class="offer-card">
  <span class="offer-price">{esc(o["price"])}</span>
  <h3>{esc(o["title"])}</h3>
  <p>{esc(o["text"])}</p>
  <a href="/contact-us/#quote" class="btn btn-primary">Claim This Offer</a>
  {f'<a class="offer-more" href="{o["link"]}">About this service &rarr;</a>' if o.get('link') else ''}
</div>''' for o in D.specials)
    return f'<div class="offers-grid" data-reveal>{cards}</div>'


def cta(ch, D, arg=None):
    """{{component:cta}}, or {{component:cta:Speech bubble text}} to have Skyler stand at the end of the
    band saying it. Use sparingly — the client doesn't want the mascot everywhere."""
    return cta_band(ch, mascot_line=arg)


def mascot(ch, D, arg=None):
    return mascot_slot(ch)


# ---- Seasonal homepage pieces (driven by site.json → season) ---------------
def _season_home(D):
    return D.season.get('home', {})


def season_badge(ch, D, arg=None):
    return _season_home(D).get('badge', 'Family-Owned Since {{founded}}').replace('{{founded}}', str(D.site['founded']))


def season_h1(ch, D, arg=None):
    return _season_home(D).get('h1', 'HVAC &amp; Air Duct Cleaning Services in <span class="hl">San Diego, CA</span>')


def season_prep(ch, D, arg=None):
    """'Get your home ready for <season>' cards. Renders nothing if the season defines none."""
    h = _season_home(D)
    if not h.get('prep'):
        return ''
    cards = []
    for i, p in enumerate(h['prep']):
        cat = D.category(p['service'])
        delay = f' style="--reveal-delay:{i * 0.08:.2f}s"' if i else ''
        cards.append(f'''<div class="prep-card" data-reveal{delay}>
  <div class="prep-top"><span class="service-icon">{icon(cat["icon"], 26)}</span><span class="prep-offer">{esc(p["offer"])}</span></div>
  <h3><a class="card-link" href="/services/{cat["slug"]}/">{esc(p["title"])}</a></h3>
  <p>{esc(p["text"])}</p>
  <span class="service-link" aria-hidden="true">Learn more &rarr;</span>
</div>''')
    return f'''<section class="section season-prep" id="winter-prep">
  <div class="container">
    <div class="section-head center" data-reveal>
      <h2>{h["prep_title"]}</h2>
      <p>{esc(h.get("prep_text", ""))}</p>
    </div>
    <div class="prep-grid">{"".join(cards)}</div>
    <p class="section-more" data-reveal><a href="{ch.tel}" class="btn btn-primary">Book Winter Service — {ch.phone}</a> <a href="/specials/" class="btn btn-outline">See Current Specials</a></p>
  </div>
</section>'''


def season_banner(ch, D, arg=None):
    """One-line seasonal banner for a service page (arg = category slug)."""
    msg = D.season.get('pages', {}).get(arg)
    if not msg:
        return ''
    return (f'<div class="season-banner"><span class="sb-icon">{icon("snow", 18)}</span><span>{esc(msg)}</span>'
            f'<a href="{ch.tel}">Call {ch.phone}</a></div>')
