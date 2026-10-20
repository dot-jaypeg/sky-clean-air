#!/usr/bin/env python3
"""Branded lead images for the 8 service pages (dev-only tool; needs Pillow).

    python3 tools/brand_service_images.py

Each category in src/data/services.json can name a real job photo in
`photo` (a public/ path). This writes public/assets/images/services/<slug>.webp
at 1200x675 with the same brand treatment as the blog images
(tools/brand_blog_images.py): gentle navy/teal grade, navy fade at the bottom,
cyan -> teal accent bar and the white SCA logo. Portrait phone photos are
shown whole on a blurred, darkened copy of themselves instead of being
cropped to 16:9, so the technician stays in frame. gen_services.py uses the
output as the page's lead image when it exists.
"""
import json
import os

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

import brand_blog_images as bb

ROOT = bb.ROOT
OUT_DIR = os.path.join(bb.PUBLIC, 'assets', 'images', 'services')
W, H = bb.W, bb.H


def fit(im):
    """Landscape → cover crop. Portrait/square → whole photo over a blurred fill."""
    if im.width / im.height >= 1.3:
        return bb.cover(im)
    bg = bb.cover(im).filter(ImageFilter.GaussianBlur(28))
    bg = ImageEnhance.Brightness(bg).enhance(0.45)
    fg = im.copy()
    fg.thumbnail((W, H), Image.LANCZOS)
    bg.paste(fg, ((W - fg.width) // 2, (H - fg.height) // 2))
    return bg


def brand(src_path):
    im = ImageOps.exif_transpose(Image.open(src_path)).convert('RGB')
    im = bb.grade(fit(im))
    mask = bb.bottom_gradient().point(lambda v: int(v * 0.7))  # lighter fade: these are the page's main photo
    im = Image.composite(Image.new('RGB', (W, H), bb.NAVY_2), im, mask)
    bar = bb.accent_bar()
    im.paste(bar, (0, H - bar.height))
    white, halo = bb.white_logo(150)
    x, y = 48, H - bar.height - 24 - white.height
    im.paste(halo, (x - 20, y - 20), halo)
    im.paste(white, (x, y), white)
    return im


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    cats = json.load(open(os.path.join(ROOT, 'src', 'data', 'services.json')))['categories']
    for c in cats:
        if not c.get('photo'):
            continue
        src = os.path.join(bb.PUBLIC, c['photo'].lstrip('/'))
        dest = os.path.join(OUT_DIR, c['slug'] + '.webp')
        brand(src).save(dest, 'WEBP', quality=bb.QUALITY, method=6)
        print(f'{c["slug"]}: {c["photo"]} -> /assets/images/services/{c["slug"]}.webp')


if __name__ == '__main__':
    main()
