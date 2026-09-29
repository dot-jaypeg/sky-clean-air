#!/usr/bin/env python3
"""Turn the raw legacy HTML (from scrape_legacy.py) into clean content JSON.

Reads   ~/Library/Caches/sky-clean-air/legacy-raw/{pages,posts}/<id>.html.gz
        content/legacy/meta/{pages,posts,categories}.json
Writes  content/legacy/{pages,posts}/<id>.json   (committed — the builder's input)
        content/legacy/images.json               (every image URL the content uses)

For Elementor pages it walks the page's own widgets in document order
(headings, text blocks, lists, FAQ accordions, images) and ignores the
site-wide header/footer, buttons, TOCs, maps and "Call Us Or Contact Us"
filler. For blog posts it takes the post-content block as-is. Everything
is sanitized to a small set of tags. Phone numbers become {{phone}} /
{{tel}} placeholders (filled from site.json at build time), and absolute
skycleanair.com links become root-relative so they point at the new site.

    python3 tools/parse_legacy.py
"""
import gzip
import html
import json
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.environ.get('LEGACY_CACHE', os.path.expanduser('~/Library/Caches/sky-clean-air/legacy-raw'))
META = os.path.join(ROOT, 'content', 'legacy', 'meta')
OUT = os.path.join(ROOT, 'content', 'legacy')

VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}


class Node:
    __slots__ = ('tag', 'attrs', 'children', 'parent')

    def __init__(self, tag, attrs=None, parent=None):
        self.tag, self.attrs, self.children, self.parent = tag, dict(attrs or {}), [], parent

    def cls(self):
        return self.attrs.get('class') or ''

    def iter(self):
        yield self
        for c in self.children:
            if isinstance(c, Node):
                yield from c.iter()

    def find(self, pred):
        return next((n for n in self.iter() if pred(n)), None)

    def find_all(self, pred):
        return [n for n in self.iter() if pred(n)]

    def text(self):
        out = []
        for c in self.children:
            out.append(c.text() if isinstance(c, Node) else c)
        return ''.join(out)


class TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node('root')
        self.cur = self.root
        self.skip = 0  # inside script/style/svg/noscript

    def handle_starttag(self, tag, attrs):
        if self.skip:
            if tag in ('script', 'style', 'svg', 'noscript'):
                self.skip += 1
            return
        if tag in ('script', 'style', 'svg', 'noscript'):
            self.skip = 1
            return
        n = Node(tag, attrs, self.cur)
        self.cur.children.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        if not self.skip and tag not in ('script', 'style', 'svg'):
            self.cur.children.append(Node(tag, attrs, self.cur))

    def handle_endtag(self, tag):
        if self.skip:
            if tag in ('script', 'style', 'svg', 'noscript'):
                self.skip -= 1
            return
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent
        if n is not self.root:
            self.cur = n.parent

    def handle_data(self, data):
        if not self.skip:
            self.cur.children.append(data)


def parse(h):
    b = TreeBuilder()
    b.feed(h)
    return b.root


# ---------------------------------------------------------------------------
# Sanitizing
# ---------------------------------------------------------------------------
ALLOWED = {
    'h2': (), 'h3': (), 'h4': (), 'p': (), 'ul': (), 'ol': (), 'li': (), 'strong': (), 'em': (),
    'b': (), 'i': (), 'a': ('href',), 'br': (), 'blockquote': (), 'table': (), 'thead': (), 'tbody': (),
    'tr': (), 'th': (), 'td': (), 'img': ('src', 'alt'), 'figure': (), 'figcaption': (),
}
RENAME = {'h1': 'h2', 'h5': 'h4', 'h6': 'h4', 'b': 'strong', 'i': 'em'}
DROP_TREE = {'form', 'button', 'iframe', 'select', 'textarea', 'input', 'nav', 'video', 'audio', 'object'}

PHONE_RE = re.compile(r'\(?\b858\)?[\s.\-]*346[\s.\-]*5551\b|\(?\b619\)?[\s.\-]*304[\s.\-]*8822\b')
TEL_RE = re.compile(r'^tel:\+?1?[\s\-.()]*(858|619)', re.I)
JUNK_TEXT = re.compile(
    r'^(call us( or contact us)?|or|contact us|need help\?.*|watch video|table of contents|read more|'
    r'get a quote|book now|call now|home|learn more|schedule (service|now)|request (a )?quote|sky clean air)[.!:]?$', re.I)

IMAGES = set()


def rewrite_href(href):
    href = (href or '').strip()
    if not href or href.startswith('#') or href.startswith('javascript'):
        return None
    if TEL_RE.match(href):
        return '{{tel}}'
    if href.startswith('mailto:') or href.startswith('tel:'):
        return href
    m = re.match(r'^https?://(www\.)?skycleanair\.com(/[^?#]*)?', href)
    if m:
        path = m.group(2) or '/'
        if '/wp-content/' in path:
            return None
        if not path.endswith('/') and '.' not in path.rsplit('/', 1)[-1]:
            path += '/'
        return path
    if href.startswith('/'):
        return href
    return href


OWN_IMG = re.compile(r'^https?://(www\.)?skycleanair\.com/wp-content/uploads/')


def clean_url(src):
    """Absolute URL of one of the client's own uploads, else None.

    A few legacy posts hotlink photos from other companies' sites; those
    aren't the client's to re-host, so they're dropped.
    """
    src = html.unescape(src or '').split('?')[0]
    return src if OWN_IMG.match(src) else None


def serialize(node, out):
    """Sanitized HTML for a node's children."""
    for c in node.children:
        if not isinstance(c, Node):
            out.append(html.escape(c, quote=False))
            continue
        tag = c.tag
        if tag in DROP_TREE:
            continue
        tag = RENAME.get(tag, tag)
        if tag == 'img':
            src = clean_url(c.attrs.get('data-src') or c.attrs.get('src'))
            if src and not re.search(r'(logo|icon|phone-call|visa|mastercard|american_express|cash|discover|badge)', src, re.I):
                IMAGES.add(src)
                alt = html.escape(c.attrs.get('alt') or '', quote=True)
                out.append(f'<img src="{html.escape(src)}" alt="{alt}" loading="lazy">')
            continue
        if tag not in ALLOWED:
            serialize(c, out)  # unwrap
            continue
        if tag == 'a':
            href = rewrite_href(c.attrs.get('href'))
            inner = []
            serialize(c, inner)
            inner = ''.join(inner)
            if not href or not inner.strip():
                out.append(inner)
            else:
                ext = '' if href.startswith(('/', '{{', 'tel:', 'mailto:')) else ' target="_blank" rel="noopener"'
                out.append(f'<a href="{href}"{ext}>{inner}</a>')
            continue
        if tag == 'br':
            out.append('<br>')
            continue
        out.append(f'<{tag}>')
        serialize(c, out)
        out.append(f'</{tag}>')


def tidy(s):
    s = PHONE_RE.sub('{{phone}}', s)
    s = s.replace('\xa0', ' ')
    s = re.sub(r'[ \t\r\n]+', ' ', s)
    s = re.sub(r'<(p|li|h[2-4]|strong|em)>\s*</\1>', '', s)
    s = re.sub(r'<p>\s*(<br>\s*)*</p>', '', s)
    s = re.sub(r'\s*(</?(?:p|ul|ol|li|h[2-4]|blockquote|table|tr|figure)>)\s*', r'\1', s)
    s = re.sub(r'(<br>\s*){2,}', '<br>', s)
    # Block-level tags on their own lines for readable output
    s = re.sub(r'(</(?:p|ul|ol|h[2-4]|blockquote|table|figure)>)', r'\1\n', s)
    return s.strip()


def to_html(node):
    out = []
    serialize(node, out)
    return tidy(''.join(out))


def plain(node):
    return re.sub(r'\s+', ' ', html.unescape(node.text() if isinstance(node, Node) else node)).strip()


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------
def has_class(n, name):
    return isinstance(n, Node) and name in n.cls().split()


def head_meta(root):
    title = root.find(lambda n: n.tag == 'title')
    desc = root.find(lambda n: n.tag == 'meta' and n.attrs.get('name') == 'description')
    og = root.find(lambda n: n.tag == 'meta' and n.attrs.get('property') == 'og:image')
    return (plain(title) if title else '', html.unescape(desc.attrs.get('content', '')) if desc else '',
            clean_url(og.attrs.get('content')) if og else None)


def widgets_in_order(container):
    """Top-level widgets (not nested inside another widget) in document order."""
    out = []

    def walk(n):
        for c in n.children:
            if not isinstance(c, Node):
                continue
            wt = c.attrs.get('data-widget_type')
            if wt:
                out.append((wt.split('.')[0], c))
            else:
                walk(c)
    walk(container)
    return out


def extract_page(root):
    page = root.find(lambda n: n.attrs.get('data-elementor-type') == 'wp-page')
    if page is None:
        # Plain (non-Elementor) page — fall back to the theme's page content wrapper.
        page = root.find(lambda n: has_class(n, 'page-content')) or root.find(lambda n: n.tag == 'main')
        if page is None:
            return '', [], None
        return to_html(page), [], None
    blocks, faqs, h1 = [], [], None
    for wt, w in widgets_in_order(page):
        if wt in ('heading', 'elementskit-heading', 'theme-post-title'):
            hn = (w.find(lambda n: n.tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'))
                  or w.find(lambda n: has_class(n, 'ekit-heading--title') or has_class(n, 'elementor-heading-title')))
            text = plain(hn or w)
            if not text or JUNK_TEXT.match(text):
                continue
            level = hn.tag if hn is not None and hn.tag.startswith('h') else 'h2'
            if level == 'h1':
                h1 = h1 or text
                continue
            level = {'h5': 'h4', 'h6': 'h4'}.get(level, level)
            if level == 'h2' and blocks and blocks[-1].startswith('<h2>'):
                level = 'h3'
            blocks.append(f'<{level}>{html.escape(PHONE_RE.sub("{{phone}}", text), quote=False)}</{level}>')
        elif wt in ('text-editor', 'theme-post-content'):
            content = to_html(w)
            text = re.sub(r'<[^>]+>', '', content).strip()
            if not text or JUNK_TEXT.match(text):
                continue
            if not content.startswith('<'):
                content = f'<p>{content}</p>'
            blocks.append(content)
        elif wt == 'icon-list':
            items = [plain(li) for li in w.find_all(lambda n: n.tag == 'li')]
            items = [i for i in items if i and not PHONE_RE.fullmatch(i.strip()) and not JUNK_TEXT.match(i)]
            if len(items) >= 2:
                blocks.append('<ul>' + ''.join(f'<li>{html.escape(PHONE_RE.sub("{{phone}}", i), quote=False)}</li>' for i in items) + '</ul>')
        elif wt == 'elementskit-accordion' or wt == 'accordion' or wt == 'toggle':
            for card in w.find_all(lambda n: has_class(n, 'elementskit-card') or has_class(n, 'elementor-accordion-item') or has_class(n, 'elementor-toggle-item')):
                q = card.find(lambda n: has_class(n, 'ekit-accordion-title') or has_class(n, 'elementor-accordion-title') or has_class(n, 'elementor-toggle-title'))
                a = card.find(lambda n: has_class(n, 'elementskit-card-body') or has_class(n, 'elementor-tab-content'))
                if q and a and plain(q):
                    ans = to_html(a)
                    if not ans.startswith('<'):
                        ans = f'<p>{ans}</p>'
                    faqs.append([PHONE_RE.sub('{{phone}}', plain(q)), ans])
        elif wt == 'image':
            img = w.find(lambda n: n.tag == 'img')
            if img is not None:
                src = clean_url(img.attrs.get('data-src') or img.attrs.get('src'))
                w_attr = int(re.sub(r'\D', '', img.attrs.get('width', '0')) or 0)
                if src and (w_attr == 0 or w_attr >= 300) and not re.search(r'(logo|icon|badge|visa|mastercard|express|cash|discover|payment)', src, re.I):
                    IMAGES.add(src)
                    alt = html.escape(img.attrs.get('alt') or '', quote=True)
                    blocks.append(f'<figure><img src="{html.escape(src)}" alt="{alt}" loading="lazy"></figure>')
    body = '\n'.join(blocks)
    # Collapse consecutive duplicate blocks (Elementor often repeats a heading in a mobile-only widget)
    lines, seen_prev = [], None
    for line in body.split('\n'):
        if line and line == seen_prev:
            continue
        lines.append(line)
        seen_prev = line
    return '\n'.join(lines), faqs, h1


def extract_post(root):
    content = root.find(lambda n: n.attrs.get('data-widget_type', '').startswith('theme-post-content'))
    if content is None:
        content = root.find(lambda n: has_class(n, 'entry-content'))
    if content is None:
        return '', []
    body = to_html(content)
    # Pull a trailing FAQ section (h2 "FAQ…" followed by h3 question / p answer pairs) into structured data
    faqs = []
    m = re.search(r'<h2>[^<]*(FAQ|Frequently Asked)[^<]*</h2>\n?(.*)$', body, re.I | re.S)
    if m:
        pairs = re.findall(r'<h3>(.*?)</h3>\n?((?:<p>.*?</p>\n?)+)', m.group(2), re.S)
        if pairs:
            faqs = [[re.sub(r'<[^>]+>', '', q).strip(), a.strip()] for q, a in pairs]
    return body, faqs


def classify(path):
    parts = path.strip('/').split('/')
    if len(parts) == 2 and parts[0] == 'service-areas':
        return 'area'
    if len(parts) == 2 and parts[0] not in ('about-us', 'hvac-air-cleaning'):
        return 'service-location'
    return 'page'


def main():
    os.makedirs(os.path.join(OUT, 'pages'), exist_ok=True)
    os.makedirs(os.path.join(OUT, 'posts'), exist_ok=True)
    cats = {c['id']: c for c in json.load(open(os.path.join(META, 'categories.json')))}
    stats = {}
    for kind in ('pages', 'posts'):
        items = json.load(open(os.path.join(META, f'{kind}.json')))
        n = 0
        for it in items:
            raw = os.path.join(CACHE, kind, f'{it["id"]}.html.gz')
            if not os.path.exists(raw):
                continue
            root = parse(gzip.open(raw).read().decode('utf-8', 'replace'))
            seo_title, desc, og_image = head_meta(root)
            path = '/' + re.sub(r'^https?://[^/]+/?', '', it['link'])
            path = html.unescape(urllib_unquote(path))
            if kind == 'pages':
                body, faqs, h1 = extract_page(root)
                typ = classify(path)
            else:
                body, faqs = extract_post(root)
                h1, typ = None, 'post'
            rec = {
                'id': it['id'], 'kind': kind[:-1], 'type': typ, 'path': path,
                'title': html.unescape(it['title']['rendered']),
                'h1': h1, 'seo_title': seo_title, 'description': PHONE_RE.sub('{{phone}}', desc),
                'date': it['date'][:10], 'modified': it['modified'][:10],
                'image': og_image, 'body': body, 'faqs': faqs,
            }
            if og_image:
                IMAGES.add(og_image)
            if kind == 'posts':
                rec['categories'] = [cats[c]['name'] for c in it.get('categories', []) if c in cats]
            with open(os.path.join(OUT, kind, f'{it["id"]}.json'), 'w') as f:
                json.dump(rec, f, ensure_ascii=False, indent=1)
            n += 1
            stats[typ] = stats.get(typ, 0) + 1
        print(f'{kind}: {n} parsed')
    with open(os.path.join(OUT, 'images.json'), 'w') as f:
        json.dump(sorted(IMAGES), f, indent=0)
    print(stats, f'{len(IMAGES)} images referenced')


def urllib_unquote(s):
    from urllib.parse import unquote
    return unquote(s)


if __name__ == '__main__':
    if len(sys.argv) > 1:  # debug: parse one cached file and print it
        kind, pid = sys.argv[1], sys.argv[2]
        root = parse(gzip.open(os.path.join(CACHE, kind, f'{pid}.html.gz')).read().decode())
        body, faqs, *_ = extract_page(root) if kind == 'pages' else extract_post(root)
        print(head_meta(root))
        print(body)
        print(json.dumps(faqs, indent=1)[:3000])
    else:
        main()
