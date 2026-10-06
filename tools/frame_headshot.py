#!/usr/bin/env python3
"""Frame a team headshot consistently for the Team page (4:5, 720x900).

Finds the person against the plain studio backdrop, then crops so that:
  - the person is centered horizontally on their body,
  - shoulders / crossed arms are fully inside the frame (with a little margin),
  - every photo has the same small headroom above the top of the head (or cap).

    python3 tools/frame_headshot.py SRC.jpg OUT.jpg [--debug DEBUG.jpg]
    python3 tools/frame_headshot.py --batch MAP.json   # {"src path": "out path", ...}

Handles EXIF rotation (camera files from the shoot are rotated).
"""
import json
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

OUT_W, OUT_H = 720, 900
HEADROOM = 0.06      # gap above the head, as a fraction of the crop height
SIDE_MARGIN = 0.10   # extra width beyond the widest part of the upper body, each side
BODY_DEPTH = 4.0     # how far below the top of the head (in head widths) to measure body width
MIN_WIDTH = 3.3      # never frame narrower than this many head widths (keeps no-cap / narrow-pose shots from zooming in)


def subject_mask(im):
    """Binary mask of 'not backdrop', at working resolution."""
    small = im.copy()
    small.thumbnail((600, 600))
    w, h = small.size
    # Backdrop colour: median of the two top corners (always background in these shots).
    patches = [small.crop((0, 0, w // 10, h // 10)), small.crop((w - w // 10, 0, w, h // 10))]
    px = sorted(p for patch in patches for p in patch.getdata())
    bg = px[len(px) // 2]
    diff = ImageChops.difference(small, Image.new('RGB', small.size, bg)).convert('L')
    mask = diff.point(lambda v: 255 if v > 38 else 0)
    # Close small holes, drop speckle.
    mask = mask.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(7)).filter(ImageFilter.MaxFilter(3))
    return mask, small.size


def rows_cols(mask):
    w, h = mask.size
    data = mask.load()
    rows = [sum(1 for x in range(w) if data[x, y]) for y in range(h)]
    return rows, data


def frame(im):
    im = ImageOps.exif_transpose(im).convert('RGB')
    W, H = im.size
    mask, (w, h) = subject_mask(im)
    rows, data = rows_cols(mask)
    min_row = max(3, int(w * 0.03))
    top = next(y for y in range(h) if rows[y] >= min_row)   # top of head / cap

    # Scale everything off head size (not a guessed crop, which would feed back on itself):
    # head width = widest row near the top (cap brim included), then measure the full upper
    # body — shoulders and crossed arms — in a band reaching about 4 head-widths down.
    head_w = max(rows[top:top + max(4, int(h * 0.06))])
    band_end = min(h, int(top + head_w * BODY_DEPTH))
    xs = sorted(x for y in range(top, band_end) for x in range(w) if data[x, y])
    # Ignore the outermost 0.5% of pixels each side (stray backdrop wrinkles/shadows).
    k = max(1, len(xs) // 200)
    left, right = xs[k], xs[-k]
    crop_w = max((right - left) * (1 + 2 * SIDE_MARGIN), head_w * MIN_WIDTH)
    crop_h = crop_w * OUT_H / OUT_W
    cx = (left + right) / 2
    y0 = top - crop_h * HEADROOM

    # Clamp: if the crop is bigger than the image allows, shrink it (keeps aspect).
    scale = min(1.0, w / crop_w, (h - max(0, y0)) / crop_h)
    crop_w *= scale
    crop_h *= scale
    x0 = min(max(0, cx - crop_w / 2), w - crop_w)
    y0 = min(max(0, y0), h - crop_h)

    f = W / w  # back to full resolution
    box = (round(x0 * f), round(y0 * f), round((x0 + crop_w) * f), round((y0 + crop_h) * f))
    return im, box


def process(src, out, debug=None):
    im, box = frame(Image.open(src))
    im.crop(box).resize((OUT_W, OUT_H), Image.LANCZOS).save(out, quality=84, optimize=True, progressive=True)
    if debug:
        d = im.copy()
        d.thumbnail((600, 600))
        s = d.width / im.width
        ImageDraw.Draw(d).rectangle([c * s for c in box], outline='red', width=3)
        d.save(debug)


if __name__ == '__main__':
    args = sys.argv[1:]
    if args and args[0] == '--batch':
        for src, out in json.load(open(args[1])).items():
            process(src, out)
            print(out)
    else:
        dbg = args[args.index('--debug') + 1] if '--debug' in args else None
        process(args[0], args[1], dbg)
