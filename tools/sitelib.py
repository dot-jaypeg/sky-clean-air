"""Shared templates for the Sky Clean Air site builder.

Everything that appears on more than one page lives here: the <head>, top
bar, header + nav, mobile drawer, footer, and the reusable content blocks
("components") that hand-written pages pull in with {{component:name}}.

Data comes from src/data/*.json (loaded once into `D` by build.py).
"""
import hashlib
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC = os.path.join(ROOT, 'public')
DATA_DIR = os.path.join(ROOT, 'src', 'data')

esc = html.escape


def load_json(name):
    with open(os.path.join(DATA_DIR, name)) as f:
        return json.load(f)


class Data:
    """All site data, loaded once."""

    def __init__(self):
        self.site = load_json('site.json')
        self.services = load_json('services.json')
        self.areas = load_json('areas.json')
        self.team = load_json('team.json')
        self.reviews = load_json('reviews.json')

    # --- services ---
    @property
    def categories(self):
        """The 8 service categories in the current season's priority order."""
        order = self.season.get('service_order') or []
        cats = self.services['categories']
        return sorted(cats, key=lambda c: order.index(c['slug']) if c['slug'] in order else len(order))

    @property
    def season(self):
        s = self.site.get('season') or {}
        return s.get(s.get('current'), {})

    @property
    def specials(self):
        cur = (self.site.get('season') or {}).get('current')
        return [o for o in self.site['specials'] if 'all' in o.get('seasons', ['all']) or cur in o.get('seasons', [])]

    def category(self, slug):
        return next(c for c in self.categories if c['slug'] == slug)

    def all_services(self):
        for c in self.categories:
            for s in c['services']:
                yield c, s

    def service(self, slug):
        return next(((c, s) for c, s in self.all_services() if s['slug'] == slug), (None, None))

    # --- areas ---
    @property
    def regions(self):
        return sorted(self.areas['regions'], key=lambda r: r['order'])

    def region(self, slug):
        return next(r for r in self.areas['regions'] if r['slug'] == slug)

    def cities(self, region_slug=None):
        cs = self.areas['cities']
        if region_slug:
            cs = [c for c in cs if c['region'] == region_slug]
        return cs


def asset_version(rel):
    """Short content hash for cache-busting ?v= query strings."""
    try:
        with open(os.path.join(PUBLIC, rel.lstrip('/')), 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()[:8]
    except FileNotFoundError:
        return '0'


# ---------------------------------------------------------------------------
# Icons — Lucide (ISC license, lucide.dev) for UI/service icons; Simple Icons (CC0) for social brands
# ---------------------------------------------------------------------------
ICONS = {
    'phone': '<path d="M13.832 16.568a1 1 0 0 0 1.213-.303l.355-.465A2 2 0 0 1 17 15h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2A18 18 0 0 1 2 4a2 2 0 0 1 2-2h3a2 2 0 0 1 2 2v3a2 2 0 0 1-.8 1.6l-.468.351a1 1 0 0 0-.292 1.233 14 14 0 0 0 6.392 6.384"/>',  # lucide: phone
    'snow': '<path d="m10 20-1.25-2.5L6 18"/> <path d="M10 4 8.75 6.5 6 6"/> <path d="m14 20 1.25-2.5L18 18"/> <path d="m14 4 1.25 2.5L18 6"/> <path d="m17 21-3-6h-4"/> <path d="m17 3-3 6 1.5 3"/> <path d="M2 12h6.5L10 9"/> <path d="m20 10-1.5 2 1.5 2"/> <path d="M22 12h-6.5L14 15"/> <path d="m4 10 1.5 2L4 14"/> <path d="m7 21 3-6-1.5-3"/> <path d="m7 3 3 6h4"/>',  # lucide: snowflake
    'vent': '<path d="M18 17.5a2.5 2.5 0 1 1-4 2.03V12"/> <path d="M6 12H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/> <path d="M6 8h12"/> <path d="M6.6 15.572A2 2 0 1 0 10 17v-5"/>',  # lucide: air-vent
    'heater': '<path d="M11 8c2-3-2-3 0-6"/> <path d="M15.5 8c2-3-2-3 0-6"/> <path d="M6 10h.01"/> <path d="M6 14h.01"/> <path d="M10 16v-4"/> <path d="M14 16v-4"/> <path d="M18 16v-4"/> <path d="M20 6a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h3"/> <path d="M5 20v2"/> <path d="M19 20v2"/>',  # lucide: heater
    'wind': '<path d="M12.8 19.6A2 2 0 1 0 14 16H2"/> <path d="M17.5 8a2.5 2.5 0 1 1 2 4H2"/> <path d="M9.8 4.4A2 2 0 1 1 11 8H2"/>',  # lucide: wind
    'dryer': '<path d="M3 6h3"/> <path d="M17 6h.01"/> <rect width="18" height="20" x="3" y="2" rx="2"/> <circle cx="12" cy="13" r="5"/> <path d="M12 18a2.5 2.5 0 0 0 0-5 2.5 2.5 0 0 1 0-5"/>',  # lucide: washing-machine
    'home': '<path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"/> <path d="M3 10a2 2 0 0 1 .709-1.528l7-6a2 2 0 0 1 2.582 0l7 6A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',  # lucide: house
    'leaf': '<path d="M11 20a10 10 0 0010-10 25.9 25.9 0 00-1.04-7.281 1 1 0 00-1.755-.325C15.833 5.5 13 5.5 9.8 6.1A7 7 0 0011 20"/> <path d="M2 21a5 5 0 012.911-4.544C7.613 15.212 8.351 15.24 11 13"/>',  # lucide: leaf
    'building': '<path d="M10 12h4"/> <path d="M10 8h4"/> <path d="M14 21v-3a2 2 0 0 0-4 0v3"/> <path d="M6 10H4a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-2"/> <path d="M6 21V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v16"/>',  # lucide: building-2
    'pin': '<path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0"/> <circle cx="12" cy="10" r="3"/>',  # lucide: map-pin
    'check': '<path d="M20 6 9 17l-5-5"/>',  # lucide: check
    'chev': '<path d="m6 9 6 6 6-6"/>',  # lucide: chevron-down
    'arrow': '<path d="M5 12h14"/> <path d="m12 5 7 7-7 7"/>',  # lucide: arrow-right
    'menu': '<path d="M4 5h16"/> <path d="M4 12h16"/> <path d="M4 19h16"/>',  # lucide: menu
    'close': '<path d="M18 6 6 18"/> <path d="m6 6 12 12"/>',  # lucide: x
    'clock': '<circle cx="12" cy="12" r="10"/> <path d="M12 6v6l4 2"/>',  # lucide: clock
    'shield': '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/> <path d="m9 12 2 2 4-4"/>',  # lucide: shield-check
    'star': '<path d="M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.123 2.123 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.123 2.123 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.122 2.122 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.122 2.122 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.122 2.122 0 0 0 1.597-1.16z"/>',  # lucide: star
    'user': '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/> <circle cx="12" cy="7" r="4"/>',  # lucide: user
    'truck': '<path d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2"/> <path d="M15 18H9"/> <path d="M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.624l-3.48-4.35A1 1 0 0 0 17.52 8H14"/> <circle cx="17" cy="18" r="2"/> <circle cx="7" cy="18" r="2"/>',  # lucide: truck
    'search': '<path d="m21 21-4.34-4.34"/> <circle cx="11" cy="11" r="8"/>',  # lucide: search
    'flame': '<path d="M12 3q1 4 4 6.5t3 5.5a1 1 0 0 1-14 0 5 5 0 0 1 1-3 1 1 0 0 0 5 0c0-2-1.5-3-1.5-5q0-2 2.5-4"/>',  # lucide: flame
    'fan': '<path d="M10.827 16.379a6.082 6.082 0 0 1-8.618-7.002l5.412 1.45a6.082 6.082 0 0 1 7.002-8.618l-1.45 5.412a6.082 6.082 0 0 1 8.618 7.002l-5.412-1.45a6.082 6.082 0 0 1-7.002 8.618l1.45-5.412Z"/> <path d="M12 12v.01"/>',  # lucide: fan
}


def badge_html(text, cls='menu-badge'):
    return f' <span class="{cls}">{esc(text)}</span>' if text else ''


def icon(name, size=24, cls=''):
    c = f' class="{cls}"' if cls else ''
    return (f'<svg{c} width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>')


SOCIAL_ICONS = {
    'Instagram': '<path d="M7.0301.084c-1.2768.0602-2.1487.264-2.911.5634-.7888.3075-1.4575.72-2.1228 1.3877-.6652.6677-1.075 1.3368-1.3802 2.127-.2954.7638-.4956 1.6365-.552 2.914-.0564 1.2775-.0689 1.6882-.0626 4.947.0062 3.2586.0206 3.6671.0825 4.9473.061 1.2765.264 2.1482.5635 2.9107.308.7889.72 1.4573 1.388 2.1228.6679.6655 1.3365 1.0743 2.1285 1.38.7632.295 1.6361.4961 2.9134.552 1.2773.056 1.6884.069 4.9462.0627 3.2578-.0062 3.668-.0207 4.9478-.0814 1.28-.0607 2.147-.2652 2.9098-.5633.7889-.3086 1.4578-.72 2.1228-1.3881.665-.6682 1.0745-1.3378 1.3795-2.1284.2957-.7632.4966-1.636.552-2.9124.056-1.2809.0692-1.6898.063-4.948-.0063-3.2583-.021-3.6668-.0817-4.9465-.0607-1.2797-.264-2.1487-.5633-2.9117-.3084-.7889-.72-1.4568-1.3876-2.1228C21.2982 1.33 20.628.9208 19.8378.6165 19.074.321 18.2017.1197 16.9244.0645 15.6471.0093 15.236-.005 11.977.0014 8.718.0076 8.31.0215 7.0301.0839m.1402 21.6932c-1.17-.0509-1.8053-.2453-2.2287-.408-.5606-.216-.96-.4771-1.3819-.895-.422-.4178-.6811-.8186-.9-1.378-.1644-.4234-.3624-1.058-.4171-2.228-.0595-1.2645-.072-1.6442-.079-4.848-.007-3.2037.0053-3.583.0607-4.848.05-1.169.2456-1.805.408-2.2282.216-.5613.4762-.96.895-1.3816.4188-.4217.8184-.6814 1.3783-.9003.423-.1651 1.0575-.3614 2.227-.4171 1.2655-.06 1.6447-.072 4.848-.079 3.2033-.007 3.5835.005 4.8495.0608 1.169.0508 1.8053.2445 2.228.408.5608.216.96.4754 1.3816.895.4217.4194.6816.8176.9005 1.3787.1653.4217.3617 1.056.4169 2.2263.0602 1.2655.0739 1.645.0796 4.848.0058 3.203-.0055 3.5834-.061 4.848-.051 1.17-.245 1.8055-.408 2.2294-.216.5604-.4763.96-.8954 1.3814-.419.4215-.8181.6811-1.3783.9-.4224.1649-1.0577.3617-2.2262.4174-1.2656.0595-1.6448.072-4.8493.079-3.2045.007-3.5825-.006-4.848-.0608M16.953 5.5864A1.44 1.44 0 1 0 18.39 4.144a1.44 1.44 0 0 0-1.437 1.4424M5.8385 12.012c.0067 3.4032 2.7706 6.1557 6.173 6.1493 3.4026-.0065 6.157-2.7701 6.1506-6.1733-.0065-3.4032-2.771-6.1565-6.174-6.1498-3.403.0067-6.156 2.771-6.1496 6.1738M8 12.0077a4 4 0 1 1 4.008 3.9921A3.9996 3.9996 0 0 1 8 12.0077"/>',  # simple-icons
    'Facebook': '<path d="M9.101 23.691v-7.98H6.627v-3.667h2.474v-1.58c0-4.085 1.848-5.978 5.858-5.978.401 0 .955.042 1.468.103a8.68 8.68 0 0 1 1.141.195v3.325a8.623 8.623 0 0 0-.653-.036 26.805 26.805 0 0 0-.733-.009c-.707 0-1.259.096-1.675.309a1.686 1.686 0 0 0-.679.622c-.258.42-.374.995-.374 1.752v1.297h3.919l-.386 2.103-.287 1.564h-3.246v8.245C19.396 23.238 24 18.179 24 12.044c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.628 3.874 10.35 9.101 11.647Z"/>',  # simple-icons
    'TikTok': '<path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/>',  # simple-icons
    'Yelp': '<path d="m7.6885 15.1415-3.6715.8483c-.3769.0871-.755.183-1.1452.155-.2611-.0188-.5122-.0414-.7606-.213a1.179 1.179 0 0 1-.331-.3594c-.3486-.5519-.3656-1.3661-.3697-2.0004a6.2874 6.2874 0 0 1 .3314-2.0642 1.857 1.857 0 0 1 .1073-.2474 2.3426 2.3426 0 0 1 .1255-.2165 2.4572 2.4572 0 0 1 .1563-.1975 1.1736 1.1736 0 0 1 .399-.2831 1.082 1.082 0 0 1 .4592-.0837c.2355.0016.5139.052.91.1734.0555.0191.1237.0382.1856.0572.3277.1013.7048.2404 1.1499.3987.6863.2404 1.3663.487 2.0463.7397l1.2117.4423c.2217.0807.4363.18.6412.297.174.0984.3273.2298.4512.387a1.217 1.217 0 0 1 .192.4309 1.2205 1.2205 0 0 1-.872 1.4522c-.0468.0151-.0852.0239-.1085.0293l-1.105.2553-.0031-.001zM18.8208 7.565a1.8506 1.8506 0 0 0-.2042-.1754 2.4082 2.4082 0 0 0-.2077-.1394 2.3607 2.3607 0 0 0-.2269-.109 1.1705 1.1705 0 0 0-.482-.0796 1.0862 1.0862 0 0 0-.4498.1263c-.2107.1048-.4388.2732-.742.5551-.042.0417-.0947.0886-.142.133-.2502.2351-.5286.5252-.8599.863a114.6363 114.6363 0 0 0-1.5166 1.5629l-.8962.9293a4.1897 4.1897 0 0 0-.4466.5483 1.541 1.541 0 0 0-.2364.5459 1.2199 1.2199 0 0 0 .0107.4518l.0046.02a1.218 1.218 0 0 0 1.4184.923 1.162 1.162 0 0 0 .1105-.0213l4.7781-1.104c.3766-.087.7587-.1667 1.097-.3631.2269-.1316.4428-.262.5909-.5252a1.1793 1.1793 0 0 0 .1405-.4683c.0733-.6512-.2668-1.3908-.5403-1.963a6.2792 6.2792 0 0 0-1.2001-1.7103zM8.9703.0754a8.6724 8.6724 0 0 0-.83.1564c-.2754.066-.548.1383-.8146.2236-.868.2844-2.0884.8063-2.295 1.8065-.1165.5655.1595 1.1439.3737 1.66.2595.6254.614 1.1889.9373 1.7777.8543 1.5545 1.7245 3.0993 2.5922 4.6457.259.4617.5416 1.0464 1.043 1.2856a1.058 1.058 0 0 0 .1013.0383c.2248.0851.4699.1016.7041.0471a4.3015 4.3015 0 0 0 .0418-.0097 1.2136 1.2136 0 0 0 .5658-.3397 1.1033 1.1033 0 0 0 .079-.0822c.3463-.435.3454-1.0833.3764-1.6134.1042-1.771.2139-3.5423.3009-5.3142.0332-.6712.1055-1.3333.0655-2.0096-.0328-.5579-.0368-1.1984-.3891-1.6563-.6218-.8073-1.9476-.741-2.8523-.6158zm2.084 15.9505a1.1053 1.1053 0 0 0-1.2306-.4145 1.1398 1.1398 0 0 0-.1526.0633 1.4806 1.4806 0 0 0-.2171.1354c-.1992.1475-.3668.3392-.5196.5315-.0386.049-.074.1143-.12.1562l-.7686 1.0573a113.9168 113.9168 0 0 0-1.2913 1.789c-.278.3895-.5184.7184-.7083 1.0094-.036.0547-.0734.116-.1075.1647-.2277.3522-.3566.6092-.4228.8381a1.0945 1.0945 0 0 0-.046.4721c.0211.1655.0768.3246.1635.467.046.0715.0957.1406.1487.207a2.334 2.334 0 0 0 .1754.1825 1.843 1.843 0 0 0 .2108.1732c.5304.369 1.1112.6342 1.722.8391a6.0958 6.0958 0 0 0 1.5716.3004c.091.0046.1821.0025.2728-.006a2.3878 2.3878 0 0 0 .2506-.0351 2.3862 2.3862 0 0 0 .2447-.071 1.1927 1.1927 0 0 0 .4175-.2658c.1127-.113.1994-.249.2541-.3989.0889-.2214.1473-.5026.1857-.92.0034-.0593.0118-.1305.0177-.1958.0304-.3463.0443-.7531.0666-1.2315.0375-.7357.067-1.4681.0903-2.2026 0 0 .0495-1.3053.0494-1.306.0113-.3008.002-.6342-.0814-.9336a1.396 1.396 0 0 0-.1756-.4054zm8.6754 2.0439c-.1605-.176-.3878-.3514-.7462-.5682-.0518-.0288-.1124-.0674-.1684-.1009-.2985-.1795-.658-.3684-1.078-.5965a120.7615 120.7615 0 0 0-1.9427-1.042l-1.1515-.6107c-.0597-.0175-.1203-.0607-.1766-.0878-.2212-.1058-.4558-.2045-.6992-.2498a1.4915 1.4915 0 0 0-.2545-.0265 1.1527 1.1527 0 0 0-.1648.01 1.1077 1.1077 0 0 0-.9227.9133 1.4186 1.4186 0 0 0 .0159.439c.0563.3065.1932.6096.3346.875l.615 1.1526c.3422.65.6884 1.2963 1.0435 1.9406.229.4202.4196.7799.5982 1.078.0338.056.0721.1163.1011.1682.2173.3584.392.584.569.7458.1146.1107.252.195.4026.247.1583.0525.326.071.4919.0546a2.368 2.368 0 0 0 .251-.0435c.0817-.022.1622-.048.241-.0784a1.863 1.863 0 0 0 .2475-.1143 6.1018 6.1018 0 0 0 1.2818-.9597c.4596-.4522.8659-.9454 1.182-1.51.044-.08.0819-.163.1138-.2483a2.49 2.49 0 0 0 .0773-.2411c.0186-.083.033-.1669.0429-.2513a1.188 1.188 0 0 0-.0565-.491 1.0933 1.0933 0 0 0-.248-.4041zm2.86 3.742a.8523.8523 0 0 1-.111.4236c-.074.132-.178.2377-.3115.3172a.8428.8428 0 0 1-.4385.119.847.847 0 0 1-.4373-.1179.8526.8526 0 0 1-.3125-.3171.8548.8548 0 0 1-.111-.4248c0-.1526.038-.2958.1143-.4294a.8405.8405 0 0 1 .315-.3159.849.849 0 0 1 .4315-.1156.8514.8514 0 0 1 .4294.1144.84.84 0 0 1 .316.3148.8494.8494 0 0 1 .1156.4317zm-.1202 0c0-.1328-.0332-.256-.0996-.3698s-.1564-.2038-.2702-.2702a.7125.7125 0 0 0-.371-.1007.7204.7204 0 0 0-.3698.0996.7487.7487 0 0 0-.2713.2702.7181.7181 0 0 0-.0996.3709c0 .132.0332.2557.0996.371a.7355.7355 0 0 0 .2713.2713.7354.7354 0 0 0 .3698.0985.7205.7205 0 0 0 .3698-.0996.7423.7423 0 0 0 .2702-.2691.7186.7186 0 0 0 .1008-.3721zm-.577.0584.2724.4522h-.1922l-.237-.4052h-.1546v.4052h-.1695v-1.02h.2988c.1268 0 .2195.0247.2783.0744.0595.0496.0892.1252.0892.2267a.2785.2785 0 0 1-.0492.1625c-.032.0466-.0775.0813-.1362.1042zm-.0412-.1408a.1532.1532 0 0 0 .056-.1214c0-.0573-.0164-.0981-.0491-.1225-.0329-.0251-.0847-.0377-.1557-.0377h-.1214v.3285h.1237c.061 0 .1098-.0157.1465-.047z"/>',  # simple-icons
}


# ---------------------------------------------------------------------------
# Page chrome
# ---------------------------------------------------------------------------
class Chrome:
    def __init__(self, D):
        self.D = D
        self.s = D.site

    # -- small helpers --
    @property
    def phone(self):
        return self.s['phone']

    @property
    def tel(self):
        return 'tel:' + self.s['phone_tel']

    def call_btn(self, label=None, cls='btn btn-primary'):
        return f'<a href="{self.tel}" class="{cls}">{esc(label or "Call Now — " + self.phone)}</a>'

    # -- head --
    def head(self, p):
        s = self.s
        title = p['title']
        desc = p.get('description', '')
        canonical = s['domain'] + p['path']
        robots = '<meta name="robots" content="noindex, follow">\n' if p.get('noindex') else ''
        extra = p.get('head_extra', '')
        css_v = asset_version('css/styles.css')
        return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(canonical)}">
{robots}<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(s['name'])}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{s['domain']}{p.get('og_image', '/assets/images/team-2026.jpg')}">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/logos/favicon-32.png">
<link rel="icon" type="image/png" sizes="192x192" href="/assets/logos/favicon-192.png">
<link rel="apple-touch-icon" href="/assets/logos/apple-touch-icon.png">
<link rel="preload" href="/assets/fonts/antonio/Antonio-Bold.ttf" as="font" type="font/ttf" crossorigin>
<link rel="stylesheet" href="/css/styles.css?v={css_v}">
{extra}{self.schema(p)}
</head>'''

    def schema(self, p):
        """LocalBusiness JSON-LD on every page (plus page-specific extras)."""
        s = self.s
        a = s['address']
        biz = {
            '@context': 'https://schema.org',
            '@type': 'HVACBusiness',
            '@id': s['domain'] + '/#business',
            'name': s['name'],
            'url': s['domain'] + '/',
            'telephone': '+1-' + s['phone'],
            'image': s['domain'] + s['logo'],
            'foundingDate': str(s['founded']),
            'address': {'@type': 'PostalAddress', 'streetAddress': a['street'], 'addressLocality': a['city'],
                        'addressRegion': a['state'], 'postalCode': a['zip'], 'addressCountry': 'US'},
            'geo': {'@type': 'GeoCoordinates', 'latitude': a['lat'], 'longitude': a['lng']},
            'openingHours': ['Mo-Fr 08:00-18:00', 'Sa 08:00-15:00'],
            'areaServed': [r['name'] for r in self.D.regions if r['status'] != 'coming-soon'],
            'sameAs': [x['url'] for x in s['socials']],
        }
        out = [biz] + p.get('schema', [])
        return '\n'.join(f'<script type="application/ld+json">{json.dumps(o, ensure_ascii=False)}</script>' for o in out)

    # -- nav model (single source for desktop dropdowns and the mobile drawer) --
    def nav(self):
        D = self.D
        # One entry per service category: (label, href, badge, icon)
        services = [(c['name'], f'/services/{c["slug"]}/', '', c['icon']) for c in D.categories]
        areas = [(r['name'], f'/service-areas/{r["slug"]}/', r.get('badge', ''), None) for r in D.regions]
        return [
            {'label': 'Services', 'href': '/services/', 'items': services, 'cls': 'services-menu'},
            {'label': 'Service Areas', 'href': '/service-areas/',
             'items': areas + [('Service Area Map', '/service-areas/#map', '', None)]},
            {'label': 'About', 'href': '/about-us/',
             'items': [('Our Story', '/about-us/', '', None), ('Our Team', '/our-team/', '', None),
                       ('Reviews', '/testimonials/', '', None), ('Careers', '/careers/', '', None),
                       ('Gallery', '/about-us/gallery/', '', None)]},
            {'label': 'Specials', 'href': '/specials/'},
            {'label': 'Blog', 'href': '/blog/'},
            {'label': 'Contact', 'href': '/contact-us/'},
        ]

    def _active(self, p, href):
        path = p['path']
        if href == '/':
            return path == '/'
        return path.startswith(href.split('#')[0])

    def header(self, p):
        s = self.s
        socials = ''.join(f'<a href="{x["url"]}" target="_blank" rel="noopener">{x["name"]}</a>' for x in s['socials'])
        a = s['address']
        nav_html = []
        for item in self.nav():
            active = ' active' if self._active(p, item['href']) else ''
            if 'items' in item:
                links = ''.join(
                    f'<a href="{h}">{f"<span class=menu-icon>{icon(ic, 16)}</span>" if ic else ""}'
                    f'<span class="menu-label">{esc(n)}</span>{badge_html(b)}</a>' for n, h, b, ic in item['items'])
                cls = f' {item["cls"]}' if item.get('cls') else ''
                nav_html.append(
                    f'<div class="nav-item has-menu"><a href="{item["href"]}" class="nav-link{active}">{item["label"]}{icon("chev", 14, "nav-chev")}</a>'
                    f'<div class="nav-menu{cls}">{links}</div></div>')
            else:
                nav_html.append(f'<div class="nav-item"><a href="{item["href"]}" class="nav-link{active}">{item["label"]}</a></div>')

        mobile = []
        for item in self.nav():
            if 'items' in item:
                sub = ''.join(f'<a href="{h}">{esc(n)}</a>' for n, h, _, _ in item['items'])
            else:
                mobile.append(f'<a class="m-link" href="{item["href"]}">{item["label"]}</a>')
                continue
            mobile.append(f'<details class="m-group"><summary>{item["label"]}{icon("chev", 18)}</summary><div class="m-sub">{sub}</div></details>')

        return f'''<div class="scroll-progress" id="scroll-progress"></div>

<div class="top-bar">
  <div class="container">
    <div class="top-bar-left">
      <span>Contractor License #{s["license"]}</span>
      <a href="/contact-us/">{esc(a["street"])}, {a["city"]}, {a["state"]} {a["zip"]}</a>
    </div>
    <div class="top-bar-social">{socials}</div>
  </div>
</div>

<header class="site-header" id="top">
  <div class="container">
    <a href="/" class="brand" aria-label="{esc(s["name"])} home">
      <img src="{s["logo"]}" alt="{esc(s["name"])} logo" width="600" height="316">
    </a>
    <nav class="main-nav" aria-label="Primary">{"".join(nav_html)}</nav>
    <div class="header-actions">
      <a href="/contact-us/#quote" class="btn btn-secondary btn-quote">Get a Quote</a>
      <a href="{self.tel}" class="btn-call">{icon("phone", 20)}<span>{self.phone}</span></a>
    </div>
    <button class="nav-toggle" aria-label="Open menu">{icon("menu", 24)}</button>
  </div>
</header>

<div class="mobile-nav" aria-hidden="true">
  <div class="mobile-nav-top">
    <a href="/"><img src="{s["logo"]}" alt="{esc(s["name"])} logo"></a>
    <button class="mobile-nav-close" aria-label="Close menu">{icon("close", 24)}</button>
  </div>
  <nav class="mobile-nav-links" aria-label="Mobile"><a class="m-link" href="/">Home</a>{"".join(mobile)}</nav>
  <div class="mobile-nav-cta">
    <a href="{self.tel}" class="btn btn-primary btn-block">Call {self.phone}</a>
    <a href="/contact-us/#quote" class="btn btn-secondary btn-block">Get a Quote</a>
  </div>
</div>

<div class="mobile-call-bar">
  <a href="{self.tel}">{icon("phone", 18)} Call Now — {self.phone}</a>
</div>'''

    def footer(self):
        s = self.s
        a = s['address']
        D = self.D
        socials = ''.join(
            f'<a href="{x["url"]}" target="_blank" rel="noopener" aria-label="{x["name"]}">'
            f'<svg width="17" height="17" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">{SOCIAL_ICONS[x["name"]]}</svg></a>'
            for x in s['socials'])
        svc = ''.join(f'<li><a href="/services/{c["slug"]}/">{esc(c["name"])}</a></li>' for c in D.categories)
        regions = ''.join(
            f'<li><a href="/service-areas/{r["slug"]}/">{esc(r["name"])}</a>{badge_html(r.get("badge"), "footer-badge")}</li>'
            for r in D.regions)
        hours = ''.join(f'<li>{d} · {h}</li>' for d, h in s['hours'] if h != 'Closed')
        options = ''.join(f'<option>{esc(c["name"])}</option>' for c in D.categories) + '<option>Other</option>'
        return f'''<footer class="site-footer" id="contact">
  <div class="footer-top">
    <div class="container footer-grid">
      <div class="footer-brand">
        <img src="{s["logo"]}" alt="{esc(s["name"])} logo">
        <p>Family-owned and operated, bringing cleaner air and dependable comfort to Southern California homes and businesses since {s["founded"]}.</p>
        <div class="footer-socials">{socials}</div>
      </div>

      <div class="footer-col">
        <h4>Services</h4>
        <ul>{svc}<li><a href="/services/">All Services</a></li></ul>
      </div>

      <div class="footer-col">
        <h4>Company</h4>
        <ul>
          <li><a href="/about-us/">About Us</a></li>
          <li><a href="/our-team/">Our Team</a></li>
          <li><a href="/testimonials/">Reviews</a></li>
          <li><a href="/specials/">Specials</a></li>
          <li><a href="/careers/">Careers</a></li>
          <li><a href="/blog/">Blog</a></li>
          <li><a href="/contact-us/">Contact</a></li>
        </ul>
        <h4 class="footer-sub">Service Areas</h4>
        <ul>{regions}</ul>
      </div>

      <div class="footer-col">
        <h4>Contact</h4>
        <ul>
          <li><a href="{self.tel}">{self.phone}</a></li>
          <li><address>{esc(a["street"])}<br>{a["city"]}, {a["state"]} {a["zip"]}</address></li>
          {hours}
          <li>Contractor License #{s["license"]}</li>
        </ul>
      </div>

      <div class="footer-col footer-form">
        <h4>Request Service</h4>
        <p class="form-lede">Tell us what's going on — we'll call you back the same day.</p>
        <form class="quote-form" data-quote-form>
          <input type="hidden" name="source" value="Footer Form"><label class="form-hp" aria-hidden="true">Website <input name="website" tabindex="-1" autocomplete="off"></label>
          <div class="form-grid">
            <div class="field full"><label for="footer-name">Name</label><input type="text" id="footer-name" name="name" placeholder="Your name" required></div>
            <div class="field full"><label for="footer-phone">Phone</label><input type="tel" id="footer-phone" name="phone" placeholder="(619) 000-0000" required></div>
            <div class="field full"><label for="footer-service">Service Needed</label>
              <select id="footer-service" name="service" required><option value="" disabled selected>Select a service</option>{options}</select></div>
          </div>
          <button type="submit" class="btn btn-primary btn-block" style="margin-top:16px;">Request a Callback</button>
          <div class="form-success">Thanks! We'll call you back shortly.</div>
        </form>
      </div>
    </div>
  </div>

  <div class="footer-bottom">
    <div class="container">
      <p>&copy; {s.get("year", 2026)} {esc(s["name"])}. All rights reserved.</p>
      <p class="footer-legal-links"><a href="/privacy-policy/">Privacy Policy</a> · <a href="/terms-conditions/">Terms &amp; Conditions</a> · <a href="/sitemap.xml">Sitemap</a></p>
    </div>
  </div>
</footer>'''

    # -- Paid-ads landing page chrome: logo + call only, no nav (keeps ad traffic focused) --
    def lp_header(self):
        s = self.s
        return f'''<header class="site-header lp-header" id="top">
  <div class="container">
    <a href="/" class="brand" aria-label="{esc(s["name"])} home"><img src="{s["logo"]}" alt="{esc(s["name"])} logo" width="600" height="316"></a>
    <div class="lp-header-right">
      <span class="lp-trust">{icon("star", 16)} 5-Star Rated · Licensed &amp; Insured</span>
      <a href="{self.tel}" class="btn-call">{icon("phone", 20)}<span>{self.phone}</span></a>
    </div>
  </div>
</header>
<div class="mobile-call-bar"><a href="{self.tel}">{icon("phone", 18)} Call Now — {self.phone}</a></div>'''

    def lp_footer(self):
        s = self.s
        a = s['address']
        return f'''<footer class="site-footer lp-footer">
  <div class="footer-bottom">
    <div class="container">
      <p>&copy; {s.get("year", 2026)} {esc(s["name"])} · {esc(a["street"])}, {a["city"]}, {a["state"]} {a["zip"]} · CA License #{s["license"]}</p>
      <p class="footer-legal-links"><a href="/privacy-policy/">Privacy Policy</a> · <a href="/terms-conditions/">Terms</a></p>
    </div>
  </div>
</footer>'''

    def page(self, p):
        body_class = ' '.join(['has-hero'] + p.get('body_class', '').split())
        js_v = asset_version('js/app.js')
        scripts = p.get('scripts', '')
        return f'''{self.head(p)}
<body class="{body_class}">

{self.lp_header() if p.get('chrome') == 'lp' else self.header(p)}

<main>
{p["body"]}
</main>

{self.lp_footer() if p.get('chrome') == 'lp' else self.footer()}

<script src="/js/app.js?v={js_v}"></script>
{scripts}
</body>
</html>
'''


# ---------------------------------------------------------------------------
# Reusable page sections
# ---------------------------------------------------------------------------
def wave(fill='#ffffff', flip=False):
    d = 'M0,50 C420,-10 1020,100 1440,30 L1440,90 L0,90 Z' if flip else 'M0,40 C360,100 1080,-10 1440,50 L1440,90 L0,90 Z'
    return (f'<div class="wave-divider" aria-hidden="true"><svg viewBox="0 0 1440 90" preserveAspectRatio="none">'
            f'<path d="{d}" fill="{fill}"/></svg></div>')


def breadcrumbs(crumbs):
    """crumbs: [(label, href or None), ...] — rendered visibly and as JSON-LD."""
    parts = []
    for i, (label, href) in enumerate(crumbs):
        if href and i < len(crumbs) - 1:
            parts.append(f'<a href="{href}">{esc(label)}</a>')
        else:
            parts.append(f'<span aria-current="page">{esc(label)}</span>')
    return '<nav class="crumbs" aria-label="Breadcrumb">' + '<span class="sep">/</span>'.join(parts) + '</nav>'


def breadcrumb_schema(domain, crumbs):
    return {
        '@context': 'https://schema.org', '@type': 'BreadcrumbList',
        'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'name': label, **({'item': domain + href} if href else {})}
            for i, (label, href) in enumerate(crumbs)
        ],
    }


def page_hero(ch, title_html, lede='', crumbs=None, kicker='', ctas=True, media=None, extra=''):
    """Dark hero band used at the top of every inner page."""
    crumbs_html = breadcrumbs(crumbs) if crumbs else ''
    kicker_html = f'<span class="hero-badge"><span class="dot"></span> {kicker}</span>' if kicker else ''
    lede_html = f'<p class="lede">{lede}</p>' if lede else ''
    cta_html = ''
    if ctas:
        cta_html = (f'<div class="hero-ctas">{ch.call_btn()}'
                    f'<a href="/contact-us/#quote" class="btn btn-secondary">Get a Quote</a></div>')
    media_html = ''
    if media:
        media_html = f'<div class="hero-media"><img src="{media}" alt="" loading="eager"></div>'
    return f'''<section class="page-hero">
  {media_html}<div class="hero-overlay"></div>
  <div class="hero-grid" aria-hidden="true"></div>
  <div class="container">
    {crumbs_html}
    <div class="hero-content">
      {kicker_html}
      <h1>{title_html}</h1>
      {lede_html}
      {cta_html}
      {extra}
    </div>
  </div>
  {wave()}
</section>'''


def cta_band(ch, title='Ready For <span class="grad-text">Cleaner Air</span>?',
             text='Get a free estimate today — same-day and next-day appointments available.', mascot_line=None):
    """Closing call-to-action band. Pass `mascot_line` to have Skyler stand at the end of the band
    with a speech bubble — opt-in per page; the client wants him used sparingly."""
    m = ch.s['mascot']
    skyler = ''
    if mascot_line and m.get('image_sm'):
        skyler = (f'<figure class="cta-skyler" aria-hidden="true"><span class="skyler-bubble">{esc(mascot_line)}</span>'
                  f'<img src="{m["image_sm"]}" alt="" width="471" height="560" loading="lazy"></figure>')
    return f'''<section class="section-tight{' cta-has-skyler' if skyler else ''}">
  <div class="container">
    <div class="cta-wrap">
      <div class="cta-band" data-reveal>
        <div class="hero-grid" aria-hidden="true"></div>
        <div>
          <h2>{title}</h2>
          <p>{text}</p>
        </div>
        <div class="cta-actions">
          {ch.call_btn("Call " + ch.phone)}
          <a href="/contact-us/#quote" class="btn btn-outline">Get a Quote</a>
        </div>
      </div>
      {skyler}
    </div>
  </div>
</section>'''


def placeholder(ch, label, note='', cls=''):
    """Labeled box marking where a pending asset goes. Hidden when show_placeholders is false."""
    if not ch.s.get('show_placeholders'):
        return ''
    note_html = f'<span class="ph-note">{esc(note)}</span>' if note else ''
    return f'<div class="asset-placeholder {cls}"><span class="ph-label">{esc(label)}</span>{note_html}</div>'


def mascot(ch, cls=''):
    """Skyler the Home Service Eagle, full size (About page panel). Opt-in only — use sparingly."""
    m = ch.s['mascot']
    if not m.get('image'):
        return ''
    return (f'<figure class="skyler-figure {cls}"><img src="{m["image"]}" alt="{esc(m["name"])}, {esc(m["title"])}, '
            f'giving a thumbs-up" width="924" height="1100" loading="lazy"></figure>')


def stars(n=5):
    return '<div class="stars" aria-label="5 out of 5 stars">' + '★' * n + '</div>'


QUOTE_SVG = ('<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 7c-1.7 0-3 1.3-3 3v4c0 1.7 1.3 3 3 3h1v-3H7c-.6 0-1-.4-1-1v-1h2c1.1 0 2-.9 2-2v-1c0-1.1-.9-2-2-2H7zm10 0c-1.7 0-3 1.3-3 3v4c0 1.7 1.3 3 3 3h1v-3h-1c-.6 0-1-.4-1-1v-1h2c1.1 0 2-.9 2-2v-1c0-1.1-.9-2-2-2h-1z"/></svg>')


def testimonial_cards(reviews):
    return ''.join(f'''<div class="testimonial-card">
  <div class="quote-icon" aria-hidden="true">{QUOTE_SVG}</div>
  {stars()}
  <p>"{esc(r["text"])}"</p>
  <div class="testimonial-author"><strong>{esc(r["name"])}</strong><span>{esc(r.get("source", "Verified Customer"))}</span></div>
</div>''' for r in reviews)


def slugify(s):
    s = s.lower().replace('&', 'and')
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return s.strip('-')
