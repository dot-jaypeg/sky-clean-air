#!/usr/bin/env python3
"""Brand the blog's lead images (dev-only tool; needs Pillow).

    python3 tools/brand_blog_images.py            # build missing / out-of-date images
    python3 tools/brand_blog_images.py --force    # rebuild everything
    python3 tools/brand_blog_images.py --sheet out.jpg [N]   # contact sheet of N results

For every image used as a legacy post's lead image (post `image` ->
content/legacy/image-map.json -> public/assets/legacy/...), writes
public/assets/blog/<name>.webp at 1200x675:

  * cover-cropped to 16:9 (portraits keep the upper part, where faces are)
  * a gentle brand grade: shadows lean toward the site's navy, a light
    cyan/teal cast in the mids, highlights and skin tones left mostly alone
  * a navy gradient rising from the bottom edge
  * a thin cyan -> teal gradient accent bar along the bottom
  * the SCA logo in white, small, bottom-left (inset far enough that the
    16:10 blog cards don't crop it)

No burned-in text. Originals are never modified. An output is skipped when
it is newer than both its source and this script, so re-runs are cheap.
gen_legacy.py picks up /assets/blog/<name>.webp automatically when it exists.
"""
import glob
import json
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC = os.path.join(ROOT, 'public')
OUT_DIR = os.path.join(PUBLIC, 'assets', 'blog')
LOGO = os.path.join(PUBLIC, 'assets', 'logos', 'sca-logo-trimmed.png')
W, H = 1200, 675
QUALITY = 78

NAVY = (6, 12, 20)        # --night
NAVY_2 = (10, 21, 36)     # --night-2
NAVY_3 = (15, 31, 51)     # --night-3
GRAD = [(0.0, (79, 184, 234)), (0.40, (42, 221, 234)), (0.75, (45, 210, 199)), (1.0, (35, 212, 215))]


def out_name(web_path):
    """/assets/legacy/2025/10/foo-1024x683.webp -> /assets/blog/foo-1024x683.webp"""
    return '/assets/blog/' + os.path.splitext(os.path.basename(web_path))[0] + '.webp'


def lead_images():
    """Unique web paths of every post lead image that was migrated."""
    imap = json.load(open(os.path.join(ROOT, 'content', 'legacy', 'image-map.json')))
    out = set()
    for f in glob.glob(os.path.join(ROOT, 'content', 'legacy', 'posts', '*.json')):
        r = json.load(open(f))
        src = r.get('image')
        if src and src in imap:
            out.add(imap[src])
    return sorted(out)


def cover(im):
    sw, sh = im.size
    scale = max(W / sw, H / sh)
    nw, nh = max(W, round(sw * scale)), max(H, round(sh * scale))
    im = im.resize((nw, nh), Image.LANCZOS)
    x = (nw - W) // 2
    # Portraits / tall crops: bias toward the top third (heads), not dead centre.
    y = int((nh - H) * (0.3 if sh > sw else 0.5))
    return im.crop((x, y, x + W, y + H))


def _lut(fn):
    return [max(0, min(255, int(round(fn(i))))) for i in range(256)]


def grade(im):
    """Subtle split-tone: lift shadows toward navy, a whisper of cyan/teal in the
    mids, highlights untouched. Applied at partial strength so skin stays natural."""
    def shadow_w(i):     # 1 in deep shadows -> 0 by the upper mids
        t = i / 255.0
        return max(0.0, 1.0 - t / 0.55) ** 1.6

    def mid_w(i):        # bell around the mids
        t = i / 255.0
        return max(0.0, 1.0 - abs(t - 0.45) / 0.45)

    # Per-channel curves (r, g, b): shadows pulled toward navy blue-black,
    # mids nudged slightly to cyan (less red, a touch more green/blue).
    r = _lut(lambda i: i - 10 * shadow_w(i) - 5 * mid_w(i))
    g = _lut(lambda i: i - 3 * shadow_w(i) + 3 * mid_w(i))
    b = _lut(lambda i: i + 10 * shadow_w(i) + 5 * mid_w(i))
    graded = im.point(r + g + b)
    # Very slight contrast lift and saturation trim to unify the set.
    graded = ImageOps.autocontrast(graded, cutoff=0.5, preserve_tone=True)
    grey = ImageOps.grayscale(graded).convert('RGB')
    graded = Image.blend(grey, graded, 0.92)
    return Image.blend(im, graded, 0.85)


def bottom_gradient():
    """Navy rising from the bottom: strong at the edge, gone by ~55% height, plus a
    faint top-left vignette so the white logo and the photo sit together."""
    mask = Image.new('L', (1, H))
    start = int(H * 0.40)
    for y in range(H):
        t = 0.0 if y < start else (y - start) / (H - start)
        mask.putpixel((0, y), int(255 * (0.93 * t ** 1.3)))
    mask = mask.resize((W, H))
    return mask


def accent_bar(h=8):
    bar = Image.new('RGB', (W, h))
    px = bar.load()
    for x in range(W):
        t = x / (W - 1)
        for i in range(len(GRAD) - 1):
            t0, c0 = GRAD[i]
            t1, c1 = GRAD[i + 1]
            if t0 <= t <= t1:
                k = (t - t0) / (t1 - t0)
                c = tuple(int(round(c0[j] + (c1[j] - c0[j]) * k)) for j in range(3))
                break
        for y in range(h):
            px[x, y] = c
    return bar


_LOGO = {}


def white_logo(width):
    if width not in _LOGO:
        src = Image.open(LOGO).convert('RGBA')
        alpha = src.getchannel('A')
        lw = width
        lh = round(src.height * lw / src.width)
        alpha = alpha.resize((lw, lh), Image.LANCZOS)
        white = Image.new('RGBA', (lw, lh), (255, 255, 255, 0))
        white.putalpha(alpha)
        # soft dark halo so the mark reads on light photos too
        halo = Image.new('RGBA', (lw + 40, lh + 40), NAVY + (0,))
        ha = Image.new('L', halo.size, 0)
        ha.paste(alpha, (20, 20))
        ha = ha.filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.55))
        halo.putalpha(ha)
        _LOGO[width] = (white, halo)
    return _LOGO[width]


_STATIC = {}


def brand(src_path):
    if not _STATIC:
        _STATIC['mask'] = bottom_gradient()
        _STATIC['navy'] = Image.new('RGB', (W, H), NAVY_2)
        _STATIC['bar'] = accent_bar()
    im = ImageOps.exif_transpose(Image.open(src_path)).convert('RGB')
    im = grade(cover(im))
    im = Image.composite(_STATIC['navy'], im, _STATIC['mask'])
    bar = _STATIC['bar']
    im.paste(bar, (0, H - bar.height))
    white, halo = white_logo(150)
    x, y = 72, H - bar.height - 26 - white.height
    im.paste(halo, (x - 20, y - 20), halo)
    im.paste(white, (x, y), white)
    return im


def build(force=False):
    os.makedirs(OUT_DIR, exist_ok=True)
    script_mtime = os.path.getmtime(os.path.abspath(__file__))
    made = skipped = missing = 0
    total_bytes = 0
    for web in lead_images():
        src = os.path.join(PUBLIC, web.lstrip('/'))
        dest = os.path.join(PUBLIC, out_name(web).lstrip('/'))
        if not os.path.exists(src):
            missing += 1
            continue
        if not force and os.path.exists(dest) and os.path.getmtime(dest) >= max(os.path.getmtime(src), script_mtime):
            skipped += 1
        else:
            brand(src).save(dest, 'WEBP', quality=QUALITY, method=6)
            made += 1
        total_bytes += os.path.getsize(dest)
    print(f'branded {made}, up to date {skipped}, missing source {missing}; '
          f'{made + skipped} files, {total_bytes / 1e6:.1f} MB in public/assets/blog/')


def contact_sheet(dest, n=12, cols=3, offset=0):
    paths = lead_images()
    step = max(1, len(paths) // n)
    picks = paths[offset::step][:n]
    tw, th = 600, 338
    rows = (len(picks) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * tw + (cols + 1) * 10, rows * (th + 24) + 10), (240, 240, 240))
    d = ImageDraw.Draw(sheet)
    for i, web in enumerate(picks):
        f = os.path.join(PUBLIC, out_name(web).lstrip('/'))
        if not os.path.exists(f):
            continue
        t = Image.open(f).convert('RGB').resize((tw, th), Image.LANCZOS)
        x, y = 10 + (i % cols) * (tw + 10), 10 + (i // cols) * (th + 24)
        sheet.paste(t, (x, y))
        d.text((x, y + th + 4), os.path.basename(f)[:80], fill=(0, 0, 0))
    sheet.save(dest, quality=88)
    print('wrote', dest)


if __name__ == '__main__':
    if '--sheet' in sys.argv:
        i = sys.argv.index('--sheet')
        args = sys.argv[i + 1:]
        contact_sheet(args[0], int(args[1]) if len(args) > 1 else 12, offset=int(args[2]) if len(args) > 2 else 0)
    else:
        build(force='--force' in sys.argv)
