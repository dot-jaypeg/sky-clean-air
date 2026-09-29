#!/usr/bin/env python3
"""Build the Sky Clean Air site into public/.

    python3 tools/build.py           # build everything
    python3 tools/build.py --check   # build, then report broken internal links

Every page is written as public/<path>/index.html so URLs keep the legacy
WordPress trailing-slash form (/air-duct-cleaning/clairemont/) and work on
any static host. Static files (css/js/assets) live in public/ directly and
are edited by hand; only the .html files, sitemap.xml and robots.txt are
generated. Generated files are tracked in public/.generated.json so pages
that disappear from the data get removed on the next build.

Page sources:
  src/pages/**/*.html   hand-written pages (front matter + HTML, see below)
  tools/gen_*.py        generators for data-driven pages (services, areas,
                        team, blog, legacy migration)

Front matter for src/pages files:

    ---
    title: About Sky Clean Air
    description: ...
    path: /about-us/
    body_class: page-about
    ---
    <section>... {{phone}} ... {{component:cta}} ...</section>
"""
import json
import os
import re
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import components  # noqa: E402
from sitelib import PUBLIC, ROOT, Chrome, Data  # noqa: E402

PAGES_DIR = os.path.join(ROOT, 'src', 'pages')
MANIFEST = os.path.join(PUBLIC, '.generated.json')


def parse_source(path):
    text = open(path, encoding='utf-8').read()
    m = re.match(r'---\n(.*?)\n---\n', text, re.S)
    if not m:
        raise ValueError(f'{path}: missing front matter')
    meta = {}
    for line in m.group(1).splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            meta[k.strip()] = v.strip()
    meta['body'] = text[m.end():]
    meta['source'] = os.path.relpath(path, ROOT)
    return meta


def expand(body, ch, D):
    """Fill {{var}} and {{component:name[:arg]}} placeholders."""
    s = D.site

    def sub(m):
        key = m.group(1).strip()
        if key.startswith('component:'):
            _, name, *arg = key.split(':', 2)
            fn = getattr(components, name.replace('-', '_'), None)
            if fn is None:
                raise KeyError(f'unknown component {name!r}')
            return fn(ch, D, arg[0] if arg else None)
        values = {
            'phone': s['phone'], 'tel': ch.tel, 'license': s['license'], 'founded': str(s['founded']),
            'years': str(date.today().year - s['founded']), 'name': s['name'],
        }
        if key not in values:
            raise KeyError(f'unknown variable {{{{{key}}}}}')
        return values[key]

    return re.sub(r'\{\{\s*([^}]+?)\s*\}\}', sub, body)


def out_path(url_path):
    rel = url_path.strip('/')
    if url_path.endswith('.html') or url_path.endswith('.xml') or url_path.endswith('.txt'):
        return os.path.join(PUBLIC, rel)
    return os.path.join(PUBLIC, rel, 'index.html') if rel else os.path.join(PUBLIC, 'index.html')


class Site:
    def __init__(self):
        self.D = Data()
        self.ch = Chrome(self.D)
        self.pages = {}   # url path -> page dict

    def add(self, p):
        path = p['path']
        if path in self.pages:
            raise ValueError(f'duplicate page {path} ({self.pages[path].get("source")} vs {p.get("source")})')
        self.pages[path] = p

    def has(self, path):
        return path in self.pages

    def build(self):
        # Hand-written pages
        for dirpath, _, files in os.walk(PAGES_DIR):
            for fn in sorted(files):
                if fn.endswith('.html'):
                    p = parse_source(os.path.join(dirpath, fn))
                    if p.get('noindex') == 'true':
                        p['noindex'] = True
                    self.add(p)

        # Generated pages — each generator gets the Site so it can check what exists.
        import generators
        for gen in generators.ALL:
            gen(self)
        for fin in generators.FINALIZE:
            fin(self)

        written = []
        for path, p in sorted(self.pages.items()):
            p['body'] = expand(p['body'], self.ch, self.D)
            html_out = self.ch.page(p) if not p.get('raw') else p['body']
            dest = out_path(path)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, 'w', encoding='utf-8') as f:
                f.write(html_out)
            written.append(os.path.relpath(dest, PUBLIC))

        written += self.write_sitemap()
        self.clean_stale(written)
        print(f'built {len(self.pages)} pages')
        return written

    def write_sitemap(self):
        domain = self.D.site['domain']
        urls = [p for path, p in sorted(self.pages.items())
                if not p.get('noindex') and not path.endswith(('.html', '.xml', '.txt'))]
        body = ['<?xml version="1.0" encoding="UTF-8"?>',
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        for p in urls:
            lastmod = f'<lastmod>{p["lastmod"]}</lastmod>' if p.get('lastmod') else ''
            body.append(f'<url><loc>{domain}{p["path"]}</loc>{lastmod}</url>')
        body.append('</urlset>')
        with open(os.path.join(PUBLIC, 'sitemap.xml'), 'w') as f:
            f.write('\n'.join(body) + '\n')
        with open(os.path.join(PUBLIC, 'robots.txt'), 'w') as f:
            f.write(f'User-agent: *\nAllow: /\n\nSitemap: {domain}/sitemap.xml\n')
        return ['sitemap.xml', 'robots.txt']

    def clean_stale(self, written):
        old = set(json.load(open(MANIFEST))) if os.path.exists(MANIFEST) else set()
        for rel in old - set(written):
            full = os.path.join(PUBLIC, rel)
            if os.path.exists(full):
                os.remove(full)
                d = os.path.dirname(full)
                while d != PUBLIC and not os.listdir(d):
                    os.rmdir(d)
                    d = os.path.dirname(d)
        with open(MANIFEST, 'w') as f:
            json.dump(sorted(written), f, indent=0)


def check_links(site):
    """Report internal links/assets that don't resolve to a built page or a file in public/."""
    broken = {}
    for path, p in site.pages.items():
        dest = out_path(path)
        html_text = open(dest, encoding='utf-8').read()
        for href in re.findall(r'(?:href|src)="(/[^"#?]*)', html_text):
            if href.startswith('//'):
                continue
            target = href if href.endswith('/') or '.' in href.rsplit('/', 1)[-1] else href + '/'
            if target in site.pages or os.path.exists(os.path.join(PUBLIC, target.lstrip('/'))):
                continue
            if os.path.exists(os.path.join(PUBLIC, target.lstrip('/'), 'index.html')):
                continue
            broken.setdefault(target, set()).add(path)
    if broken:
        print(f'\n{len(broken)} broken internal targets:')
        for t, srcs in sorted(broken.items(), key=lambda x: -len(x[1]))[:60]:
            print(f'  {t}  ({len(srcs)} pages, e.g. {sorted(srcs)[0]})')
    else:
        print('no broken internal links')
    return broken


if __name__ == '__main__':
    site = Site()
    site.build()
    if '--check' in sys.argv:
        check_links(site)
