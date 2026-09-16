# Sky Clean Air

Marketing site for Sky Clean Air (skycleanair.com) — a family-owned HVAC company serving San Diego County (San Ysidro–Fallbrook, some Temecula) and parts of Orange County (San Clemente–Brea) since 2018.

## Status

Homepage built: pure HTML/CSS/JS, no build step. This is a website refresh/redesign — other pages (services, about, gallery, contact as standalone pages) are not started yet, so nav currently links to in-page anchors.

## Structure

- `index.html` / `css/styles.css` / `js/app.js` — the homepage
- `assets/logos/` — SCA monogram logo, as provided by client
- `assets/fonts/antonio/`, `assets/fonts/inter/` — Antonio (headings) + Inter (body), self-hosted
- `assets/images/` — web-optimized photos actually used on the page (hero, story section), sourced from `assets/content/`
- `assets/content/` — client-provided team/office photos and raw video clips (videos gitignored — see below)
- `references/onboarding-info/` — full client brief: services, pricing, service area, brand contacts
- `references/website-inspo/` — reference sites for style/layout direction (samedaysd.com, Nuvehome.com, bluediamond.tech)
- `CLAUDE.md` — working agreement for this repo (design direction, git workflow, etc.)

## Design

Moody dark-navy hero with a glowing cyan/teal gradient accent (echoing the SCA logo mark), transitioning into clean light sections for trust/credibility content — structurally modeled on `lincoln-plumbing` elsewhere in the AM SITES workspace, pulling service/copy content forward from the legacy skycleanair.com site. Antonio carries headlines and labels; Inter handles body copy.

## Notes

- Brand colors: `#2addea`, `#2dd2c7`, `#23d4d7`
- `assets/content/*.mp4` and `*.mov` are gitignored — the raw clips run well over GitHub's 100MB push limit, aren't web-optimized, and turned out to be finished vertical (9:16) social-ad edits with burned-in captions rather than clean b-roll, so they aren't used as hero footage. The hero uses a real client photo instead.
- Services: HVAC install & repair, air duct cleaning, dryer vent cleaning, attic cleaning & insulation, indoor air quality
- Current promos shown on the homepage: $59 whole-house duct cleaning, $50 basic HVAC tune-up
- Phone number on the site is 619-304-8822 (per onboarding doc) — differs from the legacy site's displayed (858) 346-5551
