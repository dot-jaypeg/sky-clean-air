#!/usr/bin/env python3
"""Lint rewritten blog posts in content/blog/*.json (see tools/gen_legacy.py).

    python3 tools/check_blog_rewrites.py                 # every rewritten post
    python3 tools/check_blog_rewrites.py 1234 5678 ...   # just these post ids

Prints one line per problem ("<id> <field>: <problem>") and exits 1 if any.
Checks structure and lengths, banned AI-filler phrases, CSLB advertising wording,
markets we don't serve, prices that aren't current specials, and links.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, 'content', 'blog')

# Stock phrasing that reads as machine-written. Matched case-insensitively on word boundaries.
BANNED = [
    'delve', 'delves', 'delving', 'dive into', 'dive deep', 'deep dive', "let's dive", 'let’s dive',
    "in today's", 'in today’s', 'fast-paced world', 'fear not', 'look no further', 'in conclusion',
    'in summary', 'to sum up', 'crucial', 'crucially', 'paramount', 'vital role', 'pivotal',
    "it's important to note", 'it’s important to note', 'it is important to note', 'it is worth noting',
    'worth noting', 'navigate', 'navigating', 'navigation', 'journey', 'tapestry', 'ever-evolving',
    'ever-changing', 'realm', 'seamless', 'seamlessly', 'elevate', 'elevates', 'unlock', 'unlocking',
    'unleash', 'game-changer', 'game changer', 'robust', 'myriad', 'plethora', 'testament', 'bustling',
    'harness', 'harnessing', 'embark', 'comprehensive guide', 'ultimate guide', 'rest assured',
    'picture this', 'the good news?', 'tremendous', 'approved', 'delighted', "it's here", 'it’s here',
    'moreover', 'furthermore', 'additionally', 'in essence', 'ultimately,', 'holistic', 'synergy',
    'cutting-edge', 'state-of-the-art', 'top-notch', 'second to none', 'peace of mind',
    'a breath of fresh air', 'breathe easy', 'transformative', 'revolutionize', 'revolutionary',
    'nestled', 'boasts', 'treasure trove', 'look no further', 'say goodbye', 'say hello to',
    "whether you're a", 'whether you’re a', 'when it comes to', 'stands as', 'serves as a',
]
# Places we don't serve (the client removed the Inland Empire on 2026-10-01).
OFF_MARKET = ['inland empire', 'riverside', 'temecula', 'san bernardino', 'los angeles', 'arizona',
              'phoenix', 'gilbert', 'scottsdale', 'texas', 'florida', 'las vegas', 'nevada']
# CSLB: no insurance or bonding claims until the client confirms coverage.
CSLB = [r'\binsured\b', r'\bbonded\b', r'\binsurance\b']
ALLOWED_PRICES = {'$29', '$50', '$59'}
ALLOWED_TAGS = {'h2', 'h3', 'p', 'ul', 'ol', 'li', 'strong', 'em', 'a', 'br',
                'table', 'thead', 'tbody', 'tr', 'th', 'td'}
SERVICE_SLUGS = {'heating', 'air-conditioning', 'hvac', 'air-ducts', 'dryer-vents',
                 'indoor-air-quality', 'attic-insulation', 'commercial'}
INTERNAL_OK = re.compile(r'^/(services/(%s)/|services/|specials/|contact-us/(#quote)?|service-areas/[a-z0-9-]*/?|our-team/|about-us/|[a-z0-9-]+/)$'
                         % '|'.join(sorted(SERVICE_SLUGS)))
EMOJI = re.compile('[\U0001F300-\U0001FAFF☀-➿]')


def text_of(h):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', h)).strip()


def lint(path):
    pid = os.path.basename(path)[:-5]
    out = []

    def bad(field, msg):
        out.append('%s %s: %s' % (pid, field, msg))
    try:
        r = json.load(open(path, encoding='utf-8'))
    except Exception as e:  # noqa: BLE001 - report any parse problem
        return ['%s file: invalid JSON (%s)' % (pid, e)]
    for k in ('id', 'path', 'title', 'h1', 'description', 'quick_answer', 'body', 'faqs', 'service'):
        if not r.get(k):
            bad(k, 'missing')
    if out:
        return out
    if str(r['id']) != pid:
        bad('id', 'does not match file name')
    if len(r['title']) > 60:
        bad('title', '%d chars (max 60)' % len(r['title']))
    if not 140 <= len(r['description']) <= 158:
        bad('description', '%d chars (need 140-158)' % len(r['description']))
    qa = len(r['quick_answer'].split())
    if not 35 <= qa <= 70:
        bad('quick_answer', '%d words (need 35-70)' % qa)
    if r['service'] not in SERVICE_SLUGS:
        bad('service', 'unknown slug %r' % r['service'])
    body = r['body']
    words = len(text_of(body).split())
    if not 550 <= words <= 1500:
        bad('body', '%d words (need 550-1500)' % words)
    if len(re.findall(r'<h2\b', body)) < 3:
        bad('body', 'fewer than 3 <h2> sections')
    for tag in set(re.findall(r'</?([a-zA-Z0-9]+)', body)):
        if tag.lower() not in ALLOWED_TAGS:
            bad('body', 'tag <%s> not allowed' % tag)
    for href in re.findall(r'href="([^"]*)"', body):
        if not INTERNAL_OK.match(href):
            bad('body', 'link %r (internal links only: /services/<slug>/, /specials/, /contact-us/ ...)' % href)
    if not 3 <= len(r['faqs']) <= 6:
        bad('faqs', '%d items (need 3-6)' % len(r['faqs']))
    for q, a in r['faqs']:
        if not q.strip().endswith('?'):
            bad('faqs', 'question should end with "?": %r' % q[:60])
        if len(a.split()) > 90:
            bad('faqs', 'answer over 90 words: %r' % q[:60])
    everything = ' '.join([r['title'], r['h1'], r['description'], r['quick_answer'], text_of(body)] +
                          [q + ' ' + a for q, a in r['faqs']])
    low = everything.lower()
    for p in BANNED:
        if re.search(r'(?<![a-z])' + re.escape(p) + r'(?![a-z])', low):
            bad('copy', 'banned phrase %r' % p)
    for p in OFF_MARKET:
        if re.search(r'\b' + re.escape(p) + r'\b', low):
            bad('copy', 'off-market place %r' % p)
    for p in CSLB:
        if re.search(p, low):
            bad('copy', 'CSLB: %s wording not allowed' % p.strip('\\b'))
    for price in set(re.findall(r'\$\d[\d,]*', everything)):
        if price not in ALLOWED_PRICES:
            bad('copy', 'price %s (only current specials $29/$50/$59; otherwise say "free estimate")' % price)
    if EMOJI.search(everything):
        bad('copy', 'emoji')
    if everything.count('—') > 4:
        bad('copy', '%d em dashes (max 4; use periods or commas)' % everything.count('—'))
    if everything.count('!') > 1:
        bad('copy', '%d exclamation marks (max 1)' % everything.count('!'))
    if re.search(r'\{\{(?!phone\}\})', everything):
        bad('copy', 'template token other than {{phone}}')
    if '**' in everything or re.search(r'(^|\s)#{1,4} ', everything):
        bad('copy', 'markdown in copy')
    return out


def main(ids):
    paths = ([os.path.join(OUT_DIR, i + '.json') for i in ids] if ids
             else sorted(glob.glob(os.path.join(OUT_DIR, '*.json'))))
    paths = [p for p in paths if not os.path.basename(p).startswith('_')]
    problems = []
    for p in paths:
        if not os.path.exists(p):
            problems.append('%s file: missing' % os.path.basename(p)[:-5])
            continue
        problems += lint(p)
    for line in problems:
        print(line)
    print('%d posts checked, %d problems' % (len(paths), len(problems)), file=sys.stderr)
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
