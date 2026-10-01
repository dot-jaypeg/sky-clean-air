"""Registry of data-driven page generators, run in order by build.py.

Each generator is a function(site) that calls site.add(page_dict). A page
dict needs `path`, `title`, `description` and `body`; optional keys are
`body_class`, `noindex`, `schema` (extra JSON-LD objects), `lastmod`,
`head_extra`, `scripts`.
"""
import gen_areas
import gen_legacy
import gen_services
import gen_team
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


# Order matters a little: services and hand-built pages claim their URLs
# first, then legacy migration fills in everything else.
ALL = [
    not_found,
    gen_services.service_pages,
    gen_services.services_index,
    gen_services.service_redirects,
    gen_areas.hub,
    gen_areas.region_pages,
    gen_areas.city_pages,
    gen_team.team_page,
    gen_legacy.location_redirects,   # after city_pages: targets must exist
    gen_legacy.posts,
    gen_legacy.misc_pages,
    gen_legacy.redirects,
]

# Run after every page exists (e.g. to drop links to pages that don't).
FINALIZE = [gen_legacy.fix_legacy_links]
