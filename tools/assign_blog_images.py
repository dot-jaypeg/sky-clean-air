#!/usr/bin/env python3
"""Give every blog post its own lead image (dev-only tool; needs Pillow).

    python3 tools/assign_blog_images.py            # assign, brand, write
    python3 tools/assign_blog_images.py --sheet    # also write review contact sheets

No two posts share an image, and near-identical images (same photo, other crop
or size) count as one. The pool is:
  * every branded legacy lead image in public/assets/blog/ - its topic is the
    titles of the old posts that used it, so it lands on a related post;
  * real Sky Clean Air job photos (REAL below, tagged by hand), preferred
    over stock, branded to public/assets/blog/real-<name>.webp.
Posts are matched by topic words + service, best pairs first. The result is
written to content/blog/<id>.json -> "image" and, for Landmark-published
posts, content/blog/_landmark-images.json. Pin a choice with "image_locked":
true in a post's JSON; UNSUITABLE images are never used.
"""
import glob
import json
import os
import re
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import brand_blog_images as bb  # noqa: E402

ROOT = bb.ROOT
PUBLIC = bb.PUBLIC
BLOG = os.path.join(ROOT, 'content', 'blog')
LEGACY = os.path.join(ROOT, 'content', 'legacy')

# Genuine Sky Clean Air photos (from the 2026-10 photo inventory) and what they show.
REAL = {
    'images/gallery/after-furnace-cleaned-insulated.webp': ('heating', 'furnace plenum cleaned insulated after duct'),
    'images/gallery/before-furnace-cleaned-insulated.webp': ('air-ducts', 'dirty furnace plenum dust mold before duct'),
    'images/gallery/air-duct-cleaning-using-the-negative-pressure-method.webp': ('air-ducts', 'air duct cleaning negative pressure vacuum method process equipment happens'),
    'images/gallery/cleaning-out-rooftop-dryer-vent.webp': ('dryer-vents', 'dryer vent roof cleaning clean rooftop'),
    'images/gallery/cleaning-rooftop-hvac-unit.webp': ('commercial', 'rooftop commercial hvac unit cleaning maintenance efficiency'),
    'images/gallery/furnace-fan-deep-clean.webp': ('hvac', 'blower motor fan furnace cleaning turn'),
    'images/gallery/safely-cleaning-the-hard-to-reach-vents.webp': ('air-ducts', 'vents duct cleaning ladder professional pro'),
    'images/photos/attic-crew-protective-gear.webp': ('attic-insulation', 'attic cleaning rodent decontamination cleanup crew protective'),
    'images/photos/crew-protective-suits-vans.webp': ('attic-insulation', 'crawl space cleaning protective suits contamination'),
    'images/photos/homeowner-walkthrough.webp': ('hvac', 'inspection homeowner walkthrough questions ask buying replacing'),
    'images/photos/rooftop-ac-service.webp': ('air-conditioning', 'ac air conditioner rooftop service repair compressor'),
    'images/photos/tech-on-ladder.webp': ('air-ducts', 'air duct vent register cleaning worth'),
    'images/photos/vent-cleaning-ladder.webp': ('air-ducts', 'vent register ceiling duct cleaning dust'),
    'legacy/2022/02/ATTIC-CLEANING.webp': ('attic-insulation', 'attic cleaning clean insulation removal'),
    'legacy/2022/02/hvac-uv-cleanser-light.webp': ('indoor-air-quality', 'uv light lights air handler install worth'),
    'legacy/2023/06/15_6_24_image_image_image_203ad403-b2c2-4e3a-b1e0-f346d9a4b67b.jpg-15.jpeg-15.jpeg-15.webp':
        ('hvac', 'new furnace installation attic ducts hvac system install installation'),
    'legacy/2023/06/178_5_11_2_1675448779.961777_o_IMG_02843EE72486-185B-4833-8084-081D9AC59638_compressed.jpg.jpeg.jpeg.jpeg.webp':
        ('air-conditioning', 'condenser new ac air conditioner install size'),
    'legacy/2023/08/47_15_3_1675448759.454240_o_IMG_0269C4FAE8AB-23E6-4B26-BE2C-B42011F4E4A6_compressed.jpg.jpeg.jpeg.webp':
        ('commercial', 'commercial hvac system crane install replace cost building'),
    'legacy/2023/08/7_12_6_1675283678202.jpeg.jpeg.jpeg.webp': ('attic-insulation', 'crawl space vent protective suit cleaning'),
    'legacy/2026/07/ac-running-not-cooling-house.webp': ('air-conditioning', 'ac rooftop package unit not cooling'),
    'legacy/2026/07/ac-running-not-cooling-house-4.webp': ('air-conditioning', 'ac rooftop unit view running'),
    'legacy/2026/07/ac-running-not-cooling-house-5.webp': ('commercial', 'commercial package units replace rooftop technicians'),
    'legacy/2026/07/airflow-balancing-vs-hvac-zoning-576x1024.webp': ('hvac', 'airflow balance rooms ceiling grille return vents zone'),
    'legacy/2026/07/duct-sealing-vs-duct-cleaning.webp': ('air-ducts', 'inside dirty duct camera dust normal'),
    'legacy/2026/07/duct-sealing-vs-duct-cleaning-3.webp': ('air-ducts', 'inside duct debris lives dirty'),
    'legacy/2026/07/duct-sealing-vs-duct-cleaning-4.webp': ('air-ducts', 'flex duct sealing leaky ducts technician'),
    'legacy/2026/07/what-happens-during-hvac-tune-up.webp': ('dryer-vents', 'dryer vent cleaning vacuum equipment technician'),
    'legacy/2026/07/what-happens-during-hvac-tune-up-5.webp': ('air-conditioning', 'refrigerant gauges low recharge charge'),
    'legacy/2026/07/are-hvac-uv-lights-worth-it-cost-vs-benefits-explained-image-2.webp': ('indoor-air-quality', 'uv light lights air handler worth'),
    'legacy/2026/07/best-uv-light-for-humid-climates-stop-mold-growth-image-2.webp': ('indoor-air-quality', 'uv light mold coil humid'),
    'legacy/2026/07/coil-sterilization-vs-air-sterilization-uv-lights-guide-image-2.webp': ('indoor-air-quality', 'uv coil sterilization lights'),
    'legacy/2026/07/common-uv-light-installation-mistakes-to-avoid-today-image-2.webp': ('indoor-air-quality', 'uv light install bulb replace'),
    'legacy/2025/09/Sky-Clean-Air-Team-1-1024x577.webp': ('hvac', 'choose company hire team professional san diego'),
    'legacy/2025/01/XlvBLbQCld.webp': ('hvac', 'company van service call who'),
    'legacy/2026/07/o-4.webp': ('hvac', 'company van shop san diego'),
    'legacy/2022/03/contact-us.webp': ('air-ducts', 'company van scams look for hire'),
    'legacy/2023/07/3_25_1674593108930A300DCC3-E682-4F0E-8B1B-CE2BA869286B_compressed.jpg.jpeg.webp': ('commercial', 'company truck commercial lease service'),
}
# Never used as a lead: another company's uniform/logo, implausible AI art, text-heavy infographics.
UNSUITABLE = ('refrigerant-level-inspection-guide', 'hvac-system-performance-issues-signs', 'VMzFThzaCw',
              'ZXEuBQAvkZ', 'QZdfoDfqcg', 'cLKLKgsGPS')
STOP = set('a an and are as at be best but by can do does for from get good have how i if in is it its '
           'my of on or should so than that the their this to vs what when where which who why will with '
           'you your yourself home house homes san diego orange county southern california need know right '
           'really much many more most make makes one there they them often'.split())


def words(t):
    out = set()
    for w in re.findall(r'[a-z0-9]+', t.lower()):
        if w in STOP or len(w) < 3:
            continue
        out.add(w[:-1] if w.endswith('s') and len(w) > 4 else w)
    return out


def dhash(path):
    im = Image.open(path).convert('L').resize((9, 8), Image.LANCZOS)
    px = list(im.getdata())
    return sum(1 << i for i in range(64) if px[(i // 8) * 9 + i % 8] < px[(i // 8) * 9 + i % 8 + 1])


def pool():
    """[{src (web path), topic words, service, real}] with near-duplicates collapsed."""
    imap = json.load(open(os.path.join(LEGACY, 'image-map.json')))
    users = {}
    for f in glob.glob(os.path.join(LEGACY, 'posts', '*.json')):
        r = json.load(open(f))
        if r.get('image') in imap:
            users.setdefault(imap[r['image']], []).append(r['title'])
    from gen_legacy import match_service, _service_cats
    cats = _service_cats()
    items = []
    for web, titles in users.items():
        stem = os.path.splitext(os.path.basename(web))[0]
        branded = '/assets/blog/' + stem + '.webp'
        if stem.startswith(UNSUITABLE) or not os.path.exists(os.path.join(PUBLIC, branded.lstrip('/'))):
            continue
        name_words = '' if re.fullmatch(r'[A-Za-z]{10}', stem) else stem.replace('-', ' ')
        svc = match_service({'title': ' '.join(titles), 'seo_title': '', 'categories': [], 'body': ''}, cats)['slug']
        items.append({'src': branded, 'words': words(' '.join(titles) + ' ' + name_words), 'service': svc, 'real': False})
    for rel, (svc, tags) in REAL.items():
        src = os.path.join(PUBLIC, 'assets', rel)
        if not os.path.exists(src):
            continue
        out = '/assets/blog/real-' + os.path.splitext(os.path.basename(rel))[0][:60] + '.webp'
        dest = os.path.join(PUBLIC, out.lstrip('/'))
        if not os.path.exists(dest):
            bb.brand(src).save(dest, 'WEBP', quality=bb.QUALITY, method=6)
        items.append({'src': out, 'words': words(tags), 'service': svc, 'real': True})
    # Hand-marked duplicates (other crops of a photo already in use, outdated vans): never used.
    ex = os.path.join(BLOG, '_excluded-images.json')
    excluded = set(json.load(open(ex))) if os.path.exists(ex) else set()
    items = [i for i in items if i['src'] not in excluded]
    # Collapse near-identical images (same photo, different crop/size): keep the real/first one.
    kept, hashes = [], []
    for it in sorted(items, key=lambda i: not i['real']):
        h = dhash(os.path.join(PUBLIC, it['src'].lstrip('/')))
        if any(bin(h ^ o).count('1') <= 8 for o in hashes):
            continue
        hashes.append(h)
        kept.append(it)
    return kept


def posts():
    out = []
    for f in sorted(glob.glob(os.path.join(BLOG, '[0-9]*.json'))):
        r = json.load(open(f, encoding='utf-8'))
        out.append({'key': f, 'title': r['h1'], 'words': words(r['h1'] + ' ' + r['title']), 'service': r['service'],
                    'locked': r.get('image') if r.get('image_locked') else None})
    lm = os.path.join(ROOT, '.landmark', 'manifest.json')
    lmf = os.path.join(BLOG, '_landmark-images.json')
    lm_locked = json.load(open(lmf)) if os.path.exists(lmf) else {}
    if os.path.exists(lm):
        for rel in json.load(open(lm))['files']:
            src = os.path.join(ROOT, '.landmark', 'source', rel)
            if os.path.exists(src):
                doc = open(src, encoding='utf-8').read()
                h1 = re.search(r'<h1[^>]*>(.*?)</h1>', doc, re.S)
                title = re.sub(r'<[^>]+>', '', h1.group(1)) if h1 else rel
                svc = 'heating' if re.search(r'furnace|heat', title, re.I) else 'hvac'
                out.append({'key': '/' + os.path.dirname(rel) + '/', 'title': title, 'words': words(title),
                            'service': svc, 'locked': lm_locked.get('/' + os.path.dirname(rel) + '/'), 'landmark': True})
    return out


def assign():
    imgs, ps = pool(), posts()
    df = {}
    for i in imgs:
        for w in i['words']:
            df[w] = df.get(w, 0) + 1
    taken, result = set(), {}
    for p in ps:
        if p['locked']:
            result[p['key']] = p['locked']
            taken.add(p['locked'])
    pairs = []
    for pi, p in enumerate(ps):
        if p['key'] in result:
            continue
        for ii, i in enumerate(imgs):
            overlap = p['words'] & i['words']
            score = sum(1.0 / df[w] ** 0.5 for w in overlap) + (1.2 if i['service'] == p['service'] else 0) + \
                (0.6 if i['real'] else 0)
            pairs.append((score, pi, ii))
    pairs.sort(reverse=True)
    for score, pi, ii in pairs:
        p, i = ps[pi], imgs[ii]
        if p['key'] in result or i['src'] in taken:
            continue
        result[p['key']] = i['src']
        taken.add(i['src'])
    landmark = {}
    for p in ps:
        if p.get('landmark'):
            landmark[p['key']] = result[p['key']]
        else:
            r = json.load(open(p['key'], encoding='utf-8'))
            r['image'] = result[p['key']]
            json.dump(r, open(p['key'], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(landmark, open(os.path.join(BLOG, '_landmark-images.json'), 'w'), indent=1)
    print(f'{len(ps)} posts, {len(imgs)} distinct images in pool, {len(set(result.values()))} used, '
          f'{sum(1 for v in result.values() if "/real-" in v)} real Sky Clean Air photos')
    return ps, result


def sheets(ps, result, out_dir):
    tw, th, cols = 300, 169, 5
    rows_per = 6
    per = cols * rows_per
    for n in range(0, len(ps), per):
        chunk = ps[n:n + per]
        sheet = Image.new('RGB', (cols * tw, rows_per * (th + 34)), 'white')
        d = ImageDraw.Draw(sheet)
        for k, p in enumerate(chunk):
            im = Image.open(os.path.join(PUBLIC, result[p['key']].lstrip('/'))).convert('RGB')
            im.thumbnail((tw, th))
            x, y = (k % cols) * tw, (k // cols) * (th + 34)
            sheet.paste(im, (x, y))
            d.text((x + 3, y + th + 2), f'{n + k}: {p["title"][:46]}', fill='black')
            d.text((x + 3, y + th + 16), p['title'][46:92], fill='black')
        sheet.save(os.path.join(out_dir, f'assign-{n // per:02d}.jpg'), quality=80)


if __name__ == '__main__':
    ps, result = assign()
    if '--sheet' in sys.argv:
        out = sys.argv[sys.argv.index('--sheet') + 1] if len(sys.argv) > sys.argv.index('--sheet') + 1 else '.'
        os.makedirs(out, exist_ok=True)
        sheets(ps, result, out)


# -- branded covers ----------------------------------------------------------------
# For posts with no fitting photo in the pool: navy cover with the site grid, the
# service as a kicker, the question in Antonio, and Skyler. Unique per post.
FONTS = os.path.join(PUBLIC, 'assets', 'fonts')
SERVICE_NAMES = {'heating': 'Heating', 'air-conditioning': 'Cooling', 'hvac': 'HVAC Systems',
                 'air-ducts': 'Air Ducts', 'dryer-vents': 'Dryer Vents', 'indoor-air-quality': 'Indoor Air Quality',
                 'attic-insulation': 'Attic & Crawl Space', 'commercial': 'Commercial'}


def make_cover(title, service, dest):
    from PIL import ImageFont
    W, H = bb.W, bb.H
    im = Image.new('RGB', (W, H), bb.NAVY)
    d = ImageDraw.Draw(im)
    for y in range(H):  # night -> night-3 vertical gradient
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(bb.NAVY[k] + (bb.NAVY_3[k] - bb.NAVY[k]) * t) for k in range(3)))
    grid = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(grid)
    for x in range(0, W, 48):
        g.line([(x, 0), (x, H)], fill=(42, 221, 234, 18))
    for y in range(0, H, 48):
        g.line([(0, y), (W, y)], fill=(42, 221, 234, 18))
    glow = Image.new('L', (W, H), 0)
    ImageDraw.Draw(glow).ellipse([W - 620, -200, W + 200, 620], fill=120)
    from PIL import ImageFilter
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    im.paste(Image.new('RGB', (W, H), (42, 221, 234)), (0, 0), glow.point(lambda v: v // 3))
    im.paste(grid, (0, 0), grid)
    sky = Image.open(os.path.join(PUBLIC, 'assets', 'mascot', 'skyler-thumbs-up.webp')).convert('RGBA')
    sky.thumbnail((380, 470), Image.LANCZOS)
    im.paste(sky, (W - sky.width - 40, H - sky.height - 8), sky)
    kicker = ImageFont.truetype(os.path.join(FONTS, 'inter', 'Inter_18pt-ExtraBold.ttf'), 24)
    label = SERVICE_NAMES.get(service, 'Sky Clean Air').upper()
    d = ImageDraw.Draw(im)
    tw = d.textlength(label, font=kicker) + 2 * len(label)
    d.rounded_rectangle([72, 78, 72 + tw + 36, 124], radius=23, fill=(14, 52, 64), outline=(42, 221, 234), width=2)
    x = 90
    for ch in label:
        d.text((x, 87), ch, font=kicker, fill=(42, 221, 234))
        x += d.textlength(ch, font=kicker) + 2
    maxw = W - 72 - 430
    for size in (84, 76, 68, 60, 54, 48):
        font = ImageFont.truetype(os.path.join(FONTS, 'antonio', 'Antonio-Bold.ttf'), size)
        lines, line = [], ''
        for w in title.upper().split():
            cand = (line + ' ' + w).strip()
            if d.textlength(cand, font=font) <= maxw:
                line = cand
            else:
                lines.append(line)
                line = w
        lines.append(line)
        if len(lines) * size * 1.08 <= 350:
            break
    y = 160
    for ln in lines:
        d.text((72, y), ln, font=font, fill='white')
        y += int(size * 1.08)
    bar = bb.accent_bar()
    im.paste(bar, (0, H - bar.height))
    white, halo = bb.white_logo(150)
    lx, ly = 72, H - bar.height - 26 - white.height
    im.paste(halo, (lx - 20, ly - 20), halo)
    im.paste(white, (lx, ly), white)
    im.save(dest, 'WEBP', quality=bb.QUALITY, method=6)
