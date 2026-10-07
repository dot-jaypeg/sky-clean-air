"""Paid-ads landing pages: /lp/<region>-<service>/ (e.g. /lp/orange-county-heating/).

One page per region × seasonal service, built from src/content/landing/<oc|sd>-<service>.json.
They use the slim LP chrome (logo + call, no nav), are noindexed and left out of the sitemap,
so they don't compete with the organic service pages. Point Google/Meta ads here.
"""
import glob
import json
import os

import components
from sitelib import ROOT, esc, icon

SRC = os.path.join(ROOT, 'src', 'content', 'landing')
REGION_PREFIX = {'oc': 'orange-county', 'sd': 'san-diego-county'}
SERVICE_SLUG = {'heating': 'heating', 'air-ducts': 'air-duct-cleaning', 'dryer-vents': 'dryer-vent-cleaning'}


def lp_path(region, service):
    return f'/lp/{region}-{SERVICE_SLUG[service]}/'


def landing_pages(site):
    D, ch = site.D, site.ch
    for f in sorted(glob.glob(os.path.join(SRC, '*.json'))):
        c = json.load(open(f))
        region = D.region(c['region'])
        cat = D.category(c['service'])
        path = lp_path(c['region'], c['service'])
        offer = c.get('offer')
        offer_html = ''
        if offer:
            offer_html = f'''<div class="lp-offer"><span class="lp-offer-price">{esc(offer["price"])}</span>
  <div><strong>{esc(offer["label"])}</strong><span>{esc(offer["note"])}</span></div></div>'''
        options = ''.join(f'<option{" selected" if x["slug"] == cat["slug"] else ""}>{esc(x["name"])}</option>' for x in D.categories)
        form = f'''<div class="lp-form-card" id="quote">
  <h2>{"Claim Your " + esc(offer["label"]) if offer else "Get a Free Estimate"}</h2>
  <p>Call <a href="{{{{tel}}}}">{{{{phone}}}}</a> or send this and we'll call you back the same business day.</p>
  <form class="quote-form full-form" data-quote-form>
    <input type="hidden" name="source" value="Landing Page"><label class="form-hp" aria-hidden="true">Website <input name="website" tabindex="-1" autocomplete="off"></label>
    <div class="ff-grid">
      <div class="ff full"><label for="lp-name">Name</label><input id="lp-name" name="name" autocomplete="name" required></div>
      <div class="ff"><label for="lp-phone">Phone</label><input id="lp-phone" name="phone" type="tel" autocomplete="tel" required></div>
      <div class="ff"><label for="lp-zip">ZIP code</label><input id="lp-zip" name="zip" inputmode="numeric" autocomplete="postal-code"></div>
      <div class="ff full"><label for="lp-service">Service</label><select id="lp-service" name="service">{options}</select></div>
    </div>
    <input type="hidden" name="landing_page" value="{path}">
    <button type="submit" class="btn btn-primary btn-block">Request My Appointment</button>
    <div class="form-success">Thanks! We'll call you back shortly.</div>
  </form>
</div>'''
        why = ''.join(f'<div class="lp-why-item"><span class="service-icon">{icon(cat["icon"], 24)}</span>'
                      f'<h3>{esc(w["title"])}</h3><p>{esc(w["text"])}</p></div>' for w in c['why_now'])
        included = ''.join(f'<li>{icon("check", 18)}<span>{esc(x)}</span></li>' for x in c['included'])
        steps = ''.join(f'<li><span class="step-num">{i}</span><div><h3>{esc(st["title"])}</h3><p>{esc(st["text"])}</p></div></li>'
                        for i, st in enumerate(c['steps'], 1))
        towns = sorted(x['name'] for x in D.cities(c['region']) if x['type'] == 'city')
        faqs = ''.join(f'<details class="faq-item"><summary>{esc(q)}{icon("chev", 20)}</summary><div class="faq-a">{a}</div></details>'
                       for q, a in c['faqs'])
        body = f'''<section class="lp-hero">
  <div class="hero-overlay"></div><div class="hero-grid" aria-hidden="true"></div>
  <div class="container lp-hero-grid">
    <div class="lp-hero-copy">
      <span class="hero-badge"><span class="dot"></span> {esc(c["kicker"])}</span>
      <h1>{c["h1"]}</h1>
      <p class="lede">{esc(c["sub"])}</p>
      {offer_html}
      <div class="hero-ctas"><a href="{{{{tel}}}}" class="btn btn-primary">Call Now — {{{{phone}}}}</a></div>
      <ul class="lp-proof"><li>{icon("star", 16)} 5-star rated · ~1,000 reviews</li><li>{icon("shield", 16)} Licensed &amp; insured · CA #{{{{license}}}}</li><li>{icon("clock", 16)} Same-day &amp; next-day visits often available</li></ul>
    </div>
    {form}
  </div>
</section>
<section class="section"><div class="container"><div class="lp-why">{why}</div></div></section>
<section class="section bg-soft"><div class="container lp-two">
  <div><h2>What's <span class="grad-text">Included</span></h2><ul class="lp-included">{included}</ul></div>
  <div><h2>How It <span class="grad-text">Works</span></h2><ol class="lp-steps">{steps}</ol></div>
</div></section>
<section class="section"><div class="container"><div class="section-head center"><h2>What Our <span class="grad-text">Neighbors</span> Say</h2></div>{components.reviews(ch, D, "2")}</div></section>
<section class="section bg-soft"><div class="container lp-local">
  <h2>Serving <span class="grad-text">{esc(region["name"])}</span></h2>
  <p>{esc(c["local"])}</p>
  <p class="lp-towns">{esc(" · ".join(towns))}</p>
</div></section>
<section class="section"><div class="container narrow"><section class="faq"><h2>Questions We Hear</h2><div class="faq-list">{faqs}</div></section></div></section>
<section class="section-tight"><div class="container"><div class="cta-band">
  <div class="hero-grid" aria-hidden="true"></div>
  <div><h2>{"Book Your " + esc(offer["label"]) if offer else "Book Your Free Estimate"}</h2><p>Real people answer. Same-day and next-day appointments are often available.</p></div>
  <div class="cta-actions"><a href="{{{{tel}}}}" class="btn btn-primary">Call {{{{phone}}}}</a><a href="#quote" class="btn btn-outline">Request a Callback</a></div>
</div></div></section>'''
        site.add({
            'path': path, 'chrome': 'lp', 'noindex': True, 'body_class': 'page-lp',
            'title': c['title'] if 'Sky Clean Air' in c['title'] else c['title'] + ' | Sky Clean Air',
            'description': c['description'],
            'body': body,
        })
