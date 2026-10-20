"""Generators for content migrated from the legacy WordPress site.

Input: content/legacy/{pages,posts}/<id>.json (from tools/parse_legacy.py)
and content/legacy/image-map.json (from tools/fetch_legacy_images.py).

Every legacy URL keeps its path. Page types:
  service-location   /ac-repair/clairemont/     -> retired; redirects to /service-areas/clairemont/
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
    # Arizona (Gilbert) post with Lorem ipsum filler, not a market we serve
    '/gilbert-az-indoor-air-quality/': '/blog/',
}
# Paid-ads landing / thank-you pages: migrated but kept out of search.
NOINDEX = {'/landing-page/', '/sky-clean-air-google/', '/sky-clean-air-meta/', '/thank-you/',
           '/thank-you-google/', '/thank-you-meta/'}


@lru_cache(maxsize=None)
def _load():
    recs = {}
    for kind in ('pages', 'posts'):
        for f in sorted(glob.glob(os.path.join(LEGACY, kind, '*.json'))):  # same order on every OS
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
        for o in D.specials)
    return f'''<aside class="content-side">
  <div class="side-card side-quote">
    <h3>Get a Free Estimate</h3>
    <p>Same-day and next-day appointments. Tell us what's going on and we'll call you back.</p>
    <a href="{ch.tel}" class="btn btn-primary btn-block">{icon("phone", 18)} {ch.phone}</a>
    <form class="quote-form side-form" data-quote-form>
      <input type="hidden" name="source" value="Sidebar Form"><label class="form-hp" aria-hidden="true">Website <input name="website" tabindex="-1" autocomplete="off"></label>
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
# Blog posts + index
# ---------------------------------------------------------------------------
# Every legacy post is rendered through one template that adds, using only what
# is already in the post: a Quick Answer box (extractive, from the opening
# paragraphs), a table of contents from its H2s, a dated byline, a callout to
# the best-matching service page, BlogPosting/FAQ/breadcrumb schema, and tidy
# title/description meta. Copy hygiene (CSLB advertising rules, retired regions,
# competitor links, stray Spanish) runs at render time; the source JSON is
# never rewritten. `python3 tools/build.py` prints what hygiene changed, and
# BLOG_STATS holds the details for reporting.
POSTS_PER_PAGE = 24
BLOG_IMG = os.path.join(ROOT, 'public', 'assets', 'blog')
LANDMARK_MANIFEST = os.path.join(ROOT, '.landmark', 'manifest.json')
SERVICE_AREA = 'San Diego &amp; Orange County'
AREAS_SCHEMA = [
    {'@type': 'AdministrativeArea', 'name': 'San Diego County, California'},
    {'@type': 'AdministrativeArea', 'name': 'Orange County, California'},
]
BLOG_STATS = {}


def _stat(key, path, detail=None):
    s = BLOG_STATS.setdefault(key, {'count': 0, 'items': []})
    s['count'] += 1
    if detail is not None and len(s['items']) < 400:
        s['items'].append((path, detail))


def _text(h):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', h))).strip()


# -- copy hygiene ------------------------------------------------------------
# HVAC / duct / attic / cleaning contractors whose sites the legacy posts linked
# to as "sources". Links to them are removed: the whole sentence when it only
# exists to send readers there, otherwise just the link (text kept).
COMPETITOR_DOMAINS = {
    'accontractors.com', 'aceshvacllc.com', 'ajperri.com', 'atticprosinc.com', 'abchomeandcommercial.com',
    'bluefrosthvac.com', 'callwaldrop.com', 'climatemechanics.com', 'coit.com', 'crawlpros.com',
    'crawlspaceninja.com', 'drcrawlspace.com', 'drhvac.ca', 'ductcleaninggilbert.com', 'enviropdc.com',
    'groundworks.ca', 'happyhiller.com', 'huskyair.com', 'jdindoorcomfort.com', 'lcsheatingandcooling.com',
    'leeairservices.com', 'ongaroandsons.com', 'parkerandsons.com', 'petro.com', 'pritchardindustries.com',
    'servpro.com', 'statewideconditioninginc.com', 'summersphc.com', 'terrysacandheating.com',
    'totallycleanservices.com', 'townsendtotalenergy.com', 'therma.com', 'wolfe.construction',
}
# Unclear whether these are competitors; left alone but listed in the build report.
UNSURE_DOMAINS = {'hutchbiz.com', 'ssrfg.com', 'usstn.com', 'tcmemt.com', 'projecthvac.com', 'tricohomes.com',
                  'velappity.com', '2-10.com'}
OWN_TYPO_DOMAINS = {'skyleanair.com'}  # misspelt links to the client's own site
REFERRAL = re.compile(
    r"\b(check out|check this|visit|read more|learn more|refer to|according to|explains|external (?:link|source|resource)"
    r"|this (?:guide|article|resource|source|link|post|read|perspective|page|blog)|here\b|informative|helpful"
    r"|insights?|for (?:more|further|additional|detailed|in-depth)|guide (?:from|by)|source)", re.I)
SENT_SPLIT = re.compile(r'(?:(?<=[.!?])|(?<=[.!?]</b>)|(?<=[.!?]</i>)|(?<=[.!?]</em>)|(?<=[.!?]</strong>))\s+(?=[A-Z<“"])')
SPANISH = set('el la los las del que y en por para con una es su sus muy más como pero sin sobre este esta '
              'estos también puede pueden hogar aire limpieza servicio usted nuestro nuestra'.split())
ENGLISH = set('the and to of your is are for with that this you it'.split())

COMPLIANCE = [
    # (pattern, replacement) — CSLB: never advertise "bonded" or unspecified insurance.
    (re.compile(r'\b(fully\s+|properly\s+)?licensed,?\s+bonded,?\s+(?:and|&)\s+insured\b', re.I), r'\1licensed'),
    (re.compile(r'\bbonded\s+(?:and|&)\s+insured\b', re.I), 'licensed'),
    (re.compile(r'\b(licensed|certified)\s+(?:and|&)\s+(?:fully\s+)?insured\b', re.I), r'\1'),
    (re.compile(r'\b(licensed|certified),\s+insured,\s+and\s+', re.I), r'\1 and '),
    (re.compile(r'\binsured,\s+(licensed|certified),\s+and\s+', re.I), r'\1 and '),
    (re.compile(r'\b(licensed|certified),\s+insured\b', re.I), r'\1'),
    (re.compile(r'\b(?:and|&)\s+fully\s+insured\b', re.I), ''),
    (re.compile(r'\bfully\s+insured\s+(?:and|&)\s+', re.I), ''),
]
OWN_LICENSE = re.compile(r'\b((?:Sky Clean Air|We) (?:is|are) (?:a )?(?:fully |properly )?licensed)\b(?! \(California)')
INLAND = [
    (re.compile(r',?\s*(?:and|&|or)\s+(?:the\s+)?Inland Empire\b', re.I), ''),
    (re.compile(r'\b(?:the\s+)?Inland Empire\s*(?:,\s*|\s+(?:and|&)\s+)', re.I), ''),
]


def _domain(href):
    d = re.sub(r'^https?://', '', href).split('/')[0].lower()
    return d[4:] if d.startswith('www.') else d


def _is(d, domains):
    return any(d == x or d.endswith('.' + x) for x in domains)


def hygiene(h, path, license_no, count=True):
    """Render-time cleanup of migrated copy (text or HTML)."""
    def stat(key, detail=None):
        if count:
            _stat(key, path, detail)

    def rec(key, rep):
        def fn(m):
            out = m.expand(rep)
            stat(key, '%s -> %s' % (m.group(0), out.strip() or '(removed)'))
            return out
        return fn
    for pat, rep in COMPLIANCE:
        h = pat.sub(rec('compliance', rep), h)
    if license_no:
        h = OWN_LICENSE.sub(rec('license_added', r'\1 (California Contractor License #%s)' % license_no), h)
    for pat, rep in INLAND:
        h = pat.sub(rec('inland_empire', rep), h)
    if '<' not in h:
        return h

    # Misspelt links to our own domain -> internal links.
    def own(m):
        stat('own_domain_fixed', m.group(1))
        return '<a href="%s">' % (re.sub(r'^https?://[^/]+', '', m.group(1)) or '/')
    h = re.sub(r'<a href="(https?://(?:www\.)?skyleanair\.com[^"]*)"[^>]*>', own, h)

    for m in re.finditer(r'href="(https?://[^"]+)"', h):
        if _is(_domain(m.group(1)), UNSURE_DOMAINS):
            stat('unsure_link', _domain(m.group(1)))

    def block(m):
        tag, attrs, inner = m.group(1), m.group(2) or '', m.group(3)
        words = re.findall(r'[a-záéíóúñü]+', _text(inner).lower())
        if len(words) >= 6 and sum(w in SPANISH for w in words) / len(words) > 0.25 \
                and sum(w in ENGLISH for w in words) / len(words) < 0.05:
            stat('spanish_removed', _text(inner)[:120])
            return ''
        if not any(_is(_domain(u), COMPETITOR_DOMAINS) for u in re.findall(r'<a href="(https?://[^"]+)"', inner)):
            return m.group(0)
        out = []
        for sent in SENT_SPLIT.split(inner):
            links = [a for a in re.finditer(r'<a href="(https?://[^"]+)"[^>]*>(.*?)</a>', sent, re.S)
                     if _is(_domain(a.group(1)), COMPETITOR_DOMAINS)]
            if not links:
                out.append(sent)
                continue
            if tag in ('p', 'li'):
                plain = _text(sent)
                anchor_txt = ' '.join(_text(a.group(2)) for a in links)
                if REFERRAL.search(plain) or len(anchor_txt) >= 0.6 * max(1, len(plain)) or \
                        re.search(r'(Inc|LLC|Heating|Services|Industries|Sons|Cooling|Air)\b', anchor_txt):
                    stat('competitor_sentence_removed', '[%s] %s' % (_domain(links[0].group(1)), plain[:150]))
                    continue
            for a in links:
                stat('competitor_link_unwrapped', '[%s] %s' % (_domain(a.group(1)), _text(a.group(2))))
                sent = sent.replace(a.group(0), a.group(2))
            out.append(sent)
        new = ' '.join(s for s in out if s.strip())
        return '<%s%s>%s</%s>' % (tag, attrs, new, tag) if _text(new) else ''
    return re.sub(r'<(p|li|h[2-6])((?:\s[^>]*)?)>(.*?)</\1>', block, h, flags=re.S)


# -- service matching ----------------------------------------------------------
SERVICE_KEYWORDS = {
    'dryer-vents': [r'dryer', r'\blint\b'],
    'air-ducts': [r'\bducts?\b', r'duct ?work', r'duct cleaning', r'nadca', r'\bvents? cleaning', r'registers?'],
    'attic-insulation': [r'\battic', r'insulation', r'crawl ?space', r'rodent', r'radiant barrier'],
    'indoor-air-quality': [r'air quality', r'\biaq\b', r'purif', r'\buv\b', r'humidi', r'dehumidi', r'allerg',
                           r'asthma', r'\bmold\b', r'filters?\b', r'pollut', r'\bvoc', r'dander'],
    'heating': [r'furnace', r'heat pump', r'\bheating\b', r'\bheater', r'carbon monoxide', r'boiler'],
    'air-conditioning': [r'\bac\b', r'air condition', r'mini[- ]?split', r'ductless', r'refrigerant', r'cooling',
                         r'condenser', r'evaporator'],
    'commercial': [r'commercial', r'rooftop', r'\boffice', r'restaurant', r'business', r'lease', r'industr'],
    'hvac': [r'\bhvac\b', r'thermostat', r'zoning', r'tune[- ]?up', r'maintenance'],
}
CALLOUT_LINES = {
    'air-conditioning': 'AC not keeping up in San Diego or Orange County?',
    'hvac': 'Want an HVAC pro to take a look?',
    'heating': 'Furnace or heat pump acting up this season?',
    'air-ducts': 'Time to get your air ducts cleaned?',
    'dryer-vents': 'Dryer taking forever? Let us clear the vent.',
    'attic-insulation': 'Attic or insulation need attention?',
    'indoor-air-quality': 'Want cleaner, healthier air at home?',
    'commercial': 'Managing HVAC for a business or property?',
}


def match_service(r, cats):
    title = (r['title'] + ' ' + (r.get('seo_title') or '')).lower()
    catstr = ' '.join(html.unescape(c) for c in r.get('categories', [])).lower()
    lead = _text(r['body'][:2500]).lower()
    best, best_score = 'hvac', 0.0
    for slug, pats in SERVICE_KEYWORDS.items():
        score = 0.0
        for p in pats:
            score += 3 * min(2, len(re.findall(p, title))) + 2 * min(2, len(re.findall(p, catstr))) + \
                     0.5 * min(4, len(re.findall(p, lead)))
        if slug == 'commercial' and 'commercial' not in title and 'commercial' not in catstr:
            score = min(score, 1.0)
        if slug == 'hvac':
            score *= 0.6  # generic; only wins when nothing more specific does
        if score > best_score:
            best, best_score = slug, score
    return cats[best]


def service_callout(cat, ch):
    return (f'<aside class="post-callout" aria-label="Related service">'
            f'<div class="post-callout-icon" aria-hidden="true">{icon(cat.get("icon", "vent"), 26)}</div>'
            f'<div class="post-callout-body"><p class="post-callout-kicker">{esc(cat["name"])} · {SERVICE_AREA}</p>'
            f'<p class="post-callout-title">{esc(CALLOUT_LINES.get(cat["slug"], "Need a hand from a pro?"))}</p>'
            f'<p>{esc(cat["blurb"])} Sky Clean Air serves homes and businesses across San Diego County and Orange County.</p>'
            f'<p class="post-callout-actions"><a class="btn btn-primary btn-sm" href="/services/{cat["slug"]}/">'
            f'Explore {esc(cat["name"])} {icon("arrow", 16)}</a>'
            f'<a class="post-callout-call" href="{ch.tel}">{icon("phone", 16)} {ch.phone}</a></p></div></aside>')


# -- quick answer, TOC, meta -------------------------------------------------
FLUFF = re.compile(r"^(In today|In the world|In our|When it comes|When engaging|Have you|Are you|Do you|Did you know|"
                   r"Imagine|Welcome|In this (?:article|post|blog|guide)|Let[’']s|We[’']ll|We will|This (?:article|post|guide|blog)|"
                   r"Whether you|As (?:a|the) |If you[’']re (?:wondering|curious)|Understanding)", re.I)
META_SENT = re.compile(r"\b(this (?:guide|article|post|blog|piece)|we[’']ll|we will|we[’']re going to|in this (?:article|post|guide|blog)|"
                       r"(?:first|next|following) (?:two |few )?(?:paragraphs|sections)|additional insights|read on|keep reading|"
                       r"let[’']s|below|discover|explore|dive into|delve)\b", re.I)
STOP = set('a an the and or of to for in on is are your you how what why when do does can with at by it its be '
           'vs from this that my our'.split())


def sentences(text):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+(?=[A-Z0-9“"])', text) if s.strip()]


def quick_answer(body, title):
    """Best 40–70-word run of consecutive sentences from the opening paragraphs."""
    head = re.split(r'<h[2-4]', body, 1)[0]
    paras = [_text(p) for p in re.findall(r'<p[^>]*>(.*?)</p>', head, re.S)][:3]
    sents = [s for p in paras if '{{' not in p for s in sentences(p)][:10]
    keys = {w for w in re.findall(r'[a-z0-9]+', title.lower()) if w not in STOP and len(w) > 2}
    best, best_score = None, -99.0
    for i in range(len(sents)):
        words, j = 0, i
        while j < len(sents) and words < 40:
            words += len(sents[j].split())
            j += 1
        if not 40 <= words <= 70 or not re.search(r'[.!]$', sents[j - 1]):
            continue
        run = sents[i:j]
        txt = ' '.join(run)
        score = len(keys & set(re.findall(r'[a-z0-9]+', txt.lower()))) - 0.4 * i
        if any(META_SENT.search(s) for s in run):
            continue
        score -= 3 * sum(bool(FLUFF.match(s)) for s in run[:1]) + 1.5 * sum(s.endswith('?') for s in run)
        if score > best_score:
            best, best_score = txt, score
    return best


def slugify(t):
    return re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')[:60] or 'section'


def add_h2_ids(body):
    toc, used = [], {'faq', 'top'}

    def sub(m):
        attrs, inner = m.group(1) or '', m.group(2)
        label = _text(inner)
        idm = re.search(r'\bid="([^"]+)"', attrs)
        if idm:
            hid = idm.group(1)
        else:
            base = slugify(label)
            hid, k = base, 2
            while hid in used:
                hid, k = f'{base}-{k}', k + 1
            attrs = f' id="{hid}"' + attrs
        used.add(hid)
        toc.append((hid, label))
        return f'<h2{attrs}>{inner}</h2>'
    body = re.sub(r'<h2((?:\s[^>]*)?)>(.*?)</h2>', sub, body, flags=re.S)
    return body, toc


def toc_html(toc):
    items = ''.join(f'<li><a href="#{h}">{esc(t)}</a></li>' for h, t in toc)
    # Long outlines start collapsed so they don't push the article below the fold.
    return (f'<nav class="post-toc" aria-label="In this article"><details{" open" if len(toc) <= 8 else ""}>'
            f'<summary class="post-toc-title">In this article <span>({len(toc)} sections)</span></summary>'
            f'<ol>{items}</ol></details></nav>')


def insert_callout(body, callout):
    h2s = [m.start() for m in re.finditer(r'<h2[\s>]', body)]
    if len(h2s) >= 3:
        at = h2s[len(h2s) // 2]
    elif h2s:
        at = h2s[-1]
    else:
        return body + callout
    return body[:at] + callout + body[at:]


SUFFIX = ' | Sky Clean Air'
IMG_DIMS = ' width="1200" height="675"'


def post_title(r):
    base = re.sub(r'\s*[|–-]\s*Sky Clean Air\s*$', '', html.unescape(r.get('seo_title') or r['title'])).strip()
    short = re.split(r'\s*(?::|\s[–—-]\s|\?)\s*', base, 1)[0].strip()
    if base.endswith('?') and short == base[:-1].strip():
        short = base
    elif re.search(r'\?', base) and len(short) < len(base):
        short = short + '?'
    for cand in (base + SUFFIX, base, short + SUFFIX if len(short) >= 22 else None,
                 short if len(short) >= 22 else None):
        if cand and len(cand) <= 60:
            return cand
    return base


def fit_description(text, extra_sents=()):
    """140–158 chars, ending on a sentence or (with an ellipsis) a whole word; never mid-word."""
    text = re.sub(r'\s+', ' ', text.replace('{{phone}}', '')).strip()
    complete = bool(re.search(r'[.!?…)"”]$', text))
    if 140 <= len(text) <= 158 and complete:
        return text
    sents = sentences(text) + list(extra_sents)
    if not complete and sents:
        sents = sents[:-1] or sents  # the source was cut mid-sentence: drop the fragment
    out = ''
    for i, s in enumerate(sents):
        cand = (out + ' ' + s).strip()
        if len(cand) > 158:
            if len(out) >= 140:
                return out
            # finish on a whole word of the next sentence, marked with an ellipsis
            cut = cand[:157].rsplit(' ', 1)[0].rstrip(',;:–—-')
            return cut + '…' if len(cut) >= 139 else None
        out = cand
        if 140 <= len(out) <= 158 and i + 1 < len(sents) and len(out + ' ' + sents[i + 1]) > 158:
            return out
    if 140 <= len(out) <= 158:
        return out
    cand = (out + ' Serving San Diego & Orange County.').strip()
    return cand if 140 <= len(cand) <= 158 else None


# Lead images that show another company's uniform/logo or are implausible AI art. Posts using them
# get the branded real job photo of their matched service instead (tools/brand_service_images.py).
UNSUITABLE_LEAD = {'refrigerant-level-inspection-guide-for-san-diego-homeowners-featured', 'VMzFThzaCw',
                   'ZXEuBQAvkZ', 'QZdfoDfqcg', 'cLKLKgsGPS'}
UNSUITABLE_PREFIX = ('refrigerant-level-inspection-guide', 'hvac-system-performance-issues-signs')


@lru_cache(maxsize=None)
def _service_cats():
    return {c['slug']: c for c in json.load(open(os.path.join(ROOT, 'src', 'data', 'services.json')))['categories']}


def lead_image(r):
    """(path, branded) for a post's lead image; the branded 1200x675 version when built."""
    legacy = image_map().get(r['image']) if r.get('image') else None
    if not legacy:
        return None, False
    stem = os.path.splitext(os.path.basename(legacy))[0]
    if stem in UNSUITABLE_LEAD or stem.startswith(UNSUITABLE_PREFIX):
        slug = match_service(r, _service_cats())['slug']
        alt = f'/assets/images/services/{slug}.webp'
        if os.path.exists(os.path.join(ROOT, 'public', alt.lstrip('/'))):
            return alt, True
    branded = '/assets/blog/' + os.path.splitext(os.path.basename(legacy))[0] + '.webp'
    if os.path.exists(os.path.join(BLOG_IMG, os.path.basename(branded))):
        return branded, True
    return legacy, False


def _iso(d):
    return (d or '')[:10]


def posts(site):
    D, ch = site.D, site.ch
    domain = D.site['domain']
    license_no = D.site.get('license', '')
    cats = {c['slug']: c for c in D.categories}
    BLOG_STATS.clear()
    _CARDS.clear()
    recs = sorted(legacy_all('post'), key=lambda r: r['date'], reverse=True)
    by_cat = {}
    for r in recs:
        for c in r.get('categories', []):
            by_cat.setdefault(c, []).append(r)
    used_desc, used_title = set(), {}
    publisher = {'@type': 'Organization', '@id': domain + '/#business', 'name': D.site['name'], 'url': domain + '/',
                 'logo': {'@type': 'ImageObject', 'url': domain + D.site['logo'], 'width': 600, 'height': 316}}
    touched = 0
    for r in recs:
        if r['path'] in RETIRED:
            continue
        if site.has(r['path']):
            print(f'  ! post {r["path"]} collides with an existing page; skipped')
            continue
        path = r['path']
        img, branded = lead_image(r)
        body0 = local_images(r['body'])
        before = json.dumps([body0, [list(x) for x in r['faqs']], r['description'] or ''], ensure_ascii=False)
        body = hygiene(body0, path, license_no)
        faqs = [(hygiene(q, path, license_no), hygiene(a, path, license_no)) for q, a in r['faqs']]
        desc_src = hygiene(r['description'] or '', path, license_no)
        title = hygiene(r['title'], path, license_no)
        if json.dumps([body, [list(x) for x in faqs], desc_src], ensure_ascii=False) != before:
            touched += 1
        if img:
            body = re.sub(r'^<figure>.*?</figure>\n?', '', body)  # drop a duplicate lead image
        cat = match_service(r, cats)
        _stat('service:' + cat['slug'], path)

        qa = quick_answer(body, title)
        body, toc = add_h2_ids(body)
        body = insert_callout(body, service_callout(cat, ch))

        crumbs = [('Home', '/'), ('Blog', '/blog/'), (title, None)]
        faq_schema = faq_section(faqs)[1] if faqs else []
        related = []
        for c in r.get('categories', []):
            for o in by_cat.get(c, []):
                if o is not r and o not in related:
                    related.append(o)
        related = related[:3] or [o for o in recs[:4] if o is not r][:3]
        published, modified = _iso(r['date']), _iso(r['modified'] or r['date'])
        cat_names = ', '.join(html.unescape(c) for c in r.get('categories', [])[:2] if c not in ('Blog', 'Uncategorized'))
        meta = (f'<p class="post-meta">{icon("clock", 16)} '
                f'<span>Last updated <time datetime="{modified}">{format_date(modified)}</time></span>'
                f'<span class="post-meta-sep">·</span><span class="post-byline">By <a href="/our-team/">the Sky Clean Air Team</a></span>'
                f'{"<span class=post-meta-sep>·</span><span>" + esc(cat_names) + "</span>" if cat_names else ""}</p>')
        lead = (f'<figure class="post-lead"><img src="{img}" alt="{esc(title)}"'
                f'{IMG_DIMS if branded else ""} fetchpriority="high"></figure>') if img else ''
        qa_html = (f'<div class="post-quick-answer" id="quick-answer"><p class="post-qa-label">Quick Answer</p>'
                   f'<p class="post-qa-text">{esc(qa)}</p></div>') if qa else ''
        if qa:
            _stat('quick_answer', path)
        if len(toc) >= 3:
            _stat('toc', path)
        toc_block = toc_html(toc) if len(toc) >= 3 else ''
        rel_html = ''
        if related:
            rel_html = '<section class="related-posts"><h2>Keep Reading</h2><div class="blog-grid">' + \
                       ''.join(post_card(card_of(o)) for o in related) + '</div></section>'

        # Meta description: the post's own, else its quick answer / opening sentences; unique.
        body_sents = sentences(_text(body))[:8]
        description = None
        body_text = _text(body)
        desc_cut = desc_src and not re.search(r'[.!?…)"”]$', desc_src.strip())
        if desc_cut and _text(desc_src)[:60] in body_text[:600]:
            # WordPress trimmed the excerpt mid-sentence: rebuild it from the same opening text.
            start = body_text.index(_text(desc_src)[:60])
            desc_src = body_text[start:start + 700]
        for cand in (desc_src, qa or '', ' '.join(body_sents[:4]), ' '.join(body_sents[2:6])):
            if not cand:
                continue
            d = fit_description(cand)
            if d and d not in used_desc:
                description = d
                break
        if not description:
            description = fit_description(title.rstrip('.?!') + '. ' + ' '.join(body_sents)) or text_excerpt(r['body'], 155)
            _stat('description_fallback', path, description)
        if description != (r['description'] or ''):
            _stat('description_changed', path)
        used_desc.add(description)
        page_title = post_title(dict(r, title=title, seo_title=hygiene(r.get('seo_title') or '', path, license_no)))
        if page_title in used_title:
            _stat('title_duplicate', path, used_title[page_title])
        used_title.setdefault(page_title, path)
        if len(page_title) > 60:
            _stat('title_over_60', path, page_title)

        url = domain + path
        image_obj = ({'@type': 'ImageObject', 'url': domain + img, **({'width': 1200, 'height': 675} if branded else {})}
                     if img else None)
        article_schema = {
            '@context': 'https://schema.org', '@type': 'BlogPosting',
            'mainEntityOfPage': {'@type': 'WebPage', '@id': url},
            'url': url, 'headline': title[:110], 'description': description,
            **({'image': image_obj} if image_obj else {}),
            'datePublished': published, 'dateModified': modified,
            'author': {'@type': 'Organization', 'name': D.site['name'] + ' Team', 'url': domain + '/our-team/'},
            'publisher': publisher, 'inLanguage': 'en-US',
            'about': {'@type': 'Service', 'name': cat['name'], 'url': f'{domain}/services/{cat["slug"]}/',
                      'provider': {'@id': domain + '/#business'}, 'areaServed': AREAS_SCHEMA},
            'spatialCoverage': AREAS_SCHEMA,
            'wordCount': len(_text(body).split()),
            **({'articleSection': cat_names} if cat_names else {}),
            'speakable': {'@type': 'SpeakableSpecification',
                          'cssSelector': ['.page-hero h1'] + (['.post-qa-text'] if qa else [])},
        }
        head_extra = (f'<meta property="article:published_time" content="{published}">\n'
                      f'<meta property="article:modified_time" content="{modified}">\n'
                      '<meta name="twitter:card" content="summary_large_image">\n')
        site.add({
            'path': path, 'legacy': True, 'lastmod': modified,
            'title': page_title, 'description': description,
            'og_image': img or '/assets/images/team-2026.jpg',
            'body_class': 'page-post', 'head_extra': head_extra,
            'schema': [article_schema, breadcrumb_schema(domain, crumbs)] + faq_schema,
            'body': page_hero(ch, esc(title), '', crumbs, ctas=False, extra=meta) +
                    article_layout(f'{lead}{qa_html}{toc_block}<article class="prose">{body}</article>{rel_html}',
                                   sidebar(ch, D)) +
                    cta_band(ch),
        })
    BLOG_STATS['posts_touched_by_hygiene'] = {'count': touched, 'items': []}
    cards = [card_of(r) for r in recs if site.pages.get(r['path'], {}).get('legacy')]
    landmark = landmark_posts(site)
    blog_index(site, sorted(cards + landmark, key=lambda c: c['date'], reverse=True), landmark)
    report = ', '.join(f'{k} {v["count"]}' for k, v in sorted(BLOG_STATS.items()) if not k.startswith('service:'))
    print(f'  blog: {len(cards)} legacy + {len(landmark)} Landmark posts; {report}')


# -- Landmark-published posts --------------------------------------------------
# Landmark (an external publisher) commits finished pages straight to
# public/blog/<slug>/index.html and lists them in .landmark/manifest.json. We
# never regenerate or touch those files: each is registered as an `external`
# page (build.py skips writing it but keeps it in the sitemap and link check),
# and its title/description/date/og:image are read from its HTML for the /blog/
# index. The /blog/ page keeps Landmark's `landmark:start/end` marker list so
# its publisher can keep updating it between builds.
def _meta(doc, attr, name):
    m = re.search(r'<meta\s+%s="%s"\s+content="([^"]*)"' % (attr, re.escape(name)), doc) or \
        re.search(r'<meta\s+content="([^"]*)"\s+%s="%s"' % (attr, re.escape(name)), doc)
    return html.unescape(m.group(1)).strip() if m else ''


def landmark_posts(site):
    if not os.path.exists(LANDMARK_MANIFEST):
        return []
    domain = site.D.site['domain']
    out = []
    for rel in json.load(open(LANDMARK_MANIFEST, encoding='utf-8')).get('files', []):
        f = os.path.join(ROOT, 'public', rel)
        if not os.path.exists(f):
            print(f'  ! Landmark manifest lists missing file {rel}')
            continue
        doc = open(f, encoding='utf-8').read()
        canon = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', doc)
        path = canon.group(1).replace(domain, '') if canon and canon.group(1).startswith(domain) else \
            '/' + os.path.dirname(rel).replace(os.sep, '/') + '/'
        tm = re.search(r'<title>(.*?)</title>', doc, re.S)
        title = _meta(doc, 'property', 'og:title') or (html.unescape(tm.group(1)).strip() if tm else path)
        title = re.sub(r'\s*\|\s*Sky Clean Air\s*$', '', title)
        dm = re.search(r'"datePublished"\s*:\s*"([^"]+)"', doc)
        mm = re.search(r'"dateModified"\s*:\s*"([^"]+)"', doc)
        published = _iso(_meta(doc, 'property', 'article:published_time') or (dm.group(1) if dm else ''))
        modified = _iso(mm.group(1) if mm else published)
        desc = _meta(doc, 'name', 'description')
        if site.has(path) or site.has(path.rstrip('/') + '/'):
            print(f'  ! Landmark post {path} collides with a generated page; skipped')
            continue
        site.add({'path': path, 'external': True, 'source': '.landmark/manifest.json', 'title': title,
                  'description': desc, 'lastmod': modified or published, 'body': ''})
        out.append({'path': path, 'title': title, 'date': published or modified, 'excerpt': desc,
                    'img': _meta(doc, 'property', 'og:image'), 'branded': False, 'landmark': True})
    return out


# -- cards + index ---------------------------------------------------------------
_CARDS = {}


def card_of(r):
    if r['path'] not in _CARDS:
        img, branded = lead_image(r)
        _CARDS[r['path']] = {'path': r['path'], 'title': r['title'], 'date': _iso(r['date']), 'img': img,
                             'branded': branded, 'excerpt': text_excerpt(hygiene(r['body'], r['path'], '', count=False), 130)}
    return _CARDS[r['path']]


def format_date(d):
    import datetime
    dt = datetime.date.fromisoformat(d[:10])
    return '{} {}, {}'.format(dt.strftime('%B'), dt.day, dt.year)  # %-d is glibc/macOS-only


def post_card(c):
    if c['img']:
        dims = IMG_DIMS if c.get('branded') else ''
        img_html = f'<div class="post-card-img"><img src="{esc(c["img"])}" alt=""{dims} loading="lazy" decoding="async"></div>'
    else:
        img_html = '<div class="post-card-img post-card-noimg" aria-hidden="true"></div>'
    excerpt = c['excerpt'] if len(c['excerpt']) <= 140 else c['excerpt'][:130].rsplit(' ', 1)[0] + '…'
    return f'''<article class="post-card">
  {img_html}
  <div class="post-card-body">
    <p class="post-card-date">{format_date(c["date"])}</p>
    <h3><a class="card-link" href="{c["path"]}">{esc(c["title"])}</a></h3>
    <p>{esc(excerpt)}</p>
  </div>
</article>'''


def landmark_list(landmark):
    """Landmark's marker list (its publisher rewrites the lines between the markers)."""
    items = '\n'.join(f'<li class="landmark-entry"><a href="{c["path"]}">{esc(c["title"])}</a></li>'
                      for c in sorted(landmark, key=lambda c: c['date'], reverse=True))
    return ('<section class="landmark-posts section-tight"><div class="container">'
            '<p class="landmark-posts-title">Just published</p>\n<ul class="landmark-posts">\n'
            f'<!-- landmark:start -->\n{items}\n<!-- landmark:end -->\n</ul></div></section>')


def blog_index(site, cards, landmark=()):
    ch = site.ch
    pages = [cards[i:i + POSTS_PER_PAGE] for i in range(0, len(cards), POSTS_PER_PAGE)]
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
                              f'{len(cards):,} articles and counting.', crumbs, ctas=False) +
                    (landmark_list(landmark) if n == 1 and landmark else '') +
                    f'<section class="section"><div class="container"><div class="blog-grid">{"".join(post_card(c) for c in chunk)}</div>{nav}</div></section>' +
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
        if new:
            site.redirect(old, new)


def location_redirects(site):
    """Service × neighborhood pages (/air-duct-cleaning/clairemont/) are retired now that there's
    one page per service category: each points at that neighborhood's service-area page, which
    lists every service (or the service-area hub when the neighborhood has no page)."""
    for r in legacy_all('page', 'service-location'):
        area = r['path'].strip('/').split('/')[1]
        target = f'/service-areas/{area}/'
        site.redirect(r['path'], target if site.has(target) else '/service-areas/')


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
