"""Registry of data-driven page generators, run in order by build.py.

Each generator is a function(site) that calls site.add(page_dict). A page
dict needs `path`, `title`, `description` and `body`; optional keys are
`body_class`, `noindex`, `schema` (extra JSON-LD objects), `lastmod`,
`head_extra`, `scripts`.
"""
from sitelib import page_hero


def not_found(site):
    ch = site.ch
    site.add({
        'path': '/404.html',
        'title': 'Page Not Found | Sky Clean Air',
        'description': 'The page you were looking for could not be found.',
        'noindex': True,
        'body': page_hero(ch, 'Page <span class="hl">Not Found</span>',
                          "We couldn't find that page. Try one of the links below, or give us a call — we're happy to help.",
                          extra='<p class="hero-links"><a href="/">Home</a> · <a href="/services/">Services</a> · '
                                '<a href="/service-areas/">Service Areas</a> · <a href="/contact-us/">Contact</a></p>'),
    })


ALL = [not_found]
