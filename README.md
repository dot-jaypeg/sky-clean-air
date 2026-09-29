# Sky Clean Air

Marketing site for Sky Clean Air (skycleanair.com), a family-owned HVAC and indoor air quality company serving San Diego County and Orange County, with the Inland Empire coming next.

## Quick start

```sh
python3 tools/build.py --check            # build public/ and report broken links
python3 -m http.server 8791 -d public     # preview at http://localhost:8791
```

No dependencies beyond Python 3.8+. `public/` is the deploy root and works on any static host. Pages are written as `<path>/index.html`, so URLs match the legacy WordPress site's trailing-slash URLs.

## Structure

| Path | What it is |
|---|---|
| `src/data/site.json` | Phone, address, hours, specials, widget embed codes, mascot artwork, draft placeholders toggle |
| `src/data/services.json` | The 8 service categories (one page each) and the sub-services each covers |
| `src/data/areas.json` | Regions → cities with status and map coordinates (drives area pages, map, lists) |
| `src/data/team.json` | Team page, grouped by department |
| `src/data/reviews.json` | Fallback testimonials, used until the review widget is live |
| `src/data/area-copy.json` | Hand-written local intros for city pages without legacy copy |
| `src/pages/` | Hand-written pages (front matter + HTML + `{{component:…}}` blocks) |
| `src/content/services/` | Hand-written copy for the 8 service pages |
| `content/legacy/` | Content migrated from the old WordPress site (pages, posts, image map) |
| `tools/build.py` | The builder |
| `tools/sitelib.py`, `tools/components.py`, `tools/generators.py` | Shared chrome, reusable sections, data-driven page generators |
| `tools/scrape_legacy.py`, `parse_legacy.py`, `fetch_legacy_images.py` | Legacy-site migration pipeline (download → clean → images) |
| `tools/geocode_areas.py` | Fills in map coordinates for new cities |
| `public/css`, `public/js`, `public/assets` | Hand-edited static files |
| `assets/content/` | Raw client photos/video (not deployed; videos gitignored) |
| `references/` | Client brief and reference material |

Generated files (every `.html` in `public/`, `sitemap.xml`, `robots.txt`) should never be edited by hand. Change the source and rebuild.

## Adding things

- **A service area:** add the city (or a whole region) to `src/data/areas.json`, run `python3 tools/geocode_areas.py`, then rebuild.
- **A sub-service:** add it (with a `summary`) to its category in `src/data/services.json`; it shows in that service page's "What's included" list.
- **Widgets and mascot:** paste the embed code or artwork path into `src/data/site.json` and rebuild.
- **Before launch:** set `show_placeholders` to `false` in `site.json`.

## Design

A dark-navy hero with a glowing cyan/teal gradient accent (from the SCA logo mark) leads into clean light content sections. Antonio is used for headlines and Inter for body copy. Brand colors: `#2addea`, `#2dd2c7`, `#23d4d7`.
