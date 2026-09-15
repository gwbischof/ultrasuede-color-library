#!/usr/bin/env python3
"""Build ../lamous-th.json from Mitokuya's Lamous®-TH catalogue page.

Lamous® is a Japanese suede-like artificial leather, a different product from
Toray's Ultrasuede — it is in this library because it is the same kind of cloth
bought for the same kind of work, not because it is the same brand.

The source is one page: 美徳屋 (Mitokuya), a Japanese retailer, which lists the
whole TH grade as a colour picker on a single product. The page states outright
that the grade has 49 colours ("49色取り揃え"), and the picker lists exactly 49,
so the coverage question that hangs over the LX import does not arise here.

Two passes, like the other builders:

    python3 scraping/build_lamous_th.py --fetch   # snapshot page + photos
    python3 scraping/build_lamous_th.py           # sample colours, write JSON

Three things differ from LX, all forced by the source:

  * Colours have NO NAMES. The picker and the cart both identify a colour by
    its code alone ("カラー: TH431"), so `name` is the code. Inventing names
    would be inventing data.

  * The photographs carry a caption bar across the bottom with the code printed
    on it. It sits at 85-90% of frame height on all 49, so they are cropped to
    the top 84% on the way in — the bar is the seller's overlay, not the cloth,
    and leaving it in would put it in the tile as well as in the sample.

  * NO NAP BLOCK. The photographs are ~256px and ~197px once the caption is
    off, well under build_dataset's NAP_MEASURABLE of 300, so contrast cannot
    be measured. It could be *modelled* from NAP_FIT, but that curve was fitted
    on Ultrasuede LT, and applying it here would assert that a different
    manufacturer's fabric follows the same contrast-against-lightness
    relationship — which nothing here has measured. So Lamous entries carry no
    nap and the site draws their photographs instead, which is what the
    fallback in demo.js is for.
"""

import argparse
import html
import json
import pathlib
import re
import sys
import time
import urllib.request

import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / 'scraping' / 'lamous_th_page.html'
IMAGES = ROOT / 'images'
IMAGES_LARGE = IMAGES / 'large'
OUT = ROOT / 'lamous-th.json'

PAGE = 'https://mitokuya.co.jp/shop/detail.html?item_number=1&sku1=44'
ITEM_BASE = 'https://mitokuya.co.jp/items/1/'

# Caption bar starts at 85.3%-90.1% of frame height across all 49; 84% clears
# it everywhere with margin to spare.
KEEP = 0.84
SMALL_EDGE = 100

UA = 'ultrasuede-color-library/1.0 (+https://github.com/gwbischof/ultrasuede-color-library)'


def get(url, binary=False):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = r.read()
    return d if binary else d.decode('utf-8')


def parse_page(text):
    """The colour picker: [(sku1, code, image filename)], in page order."""
    m = re.search(r'<div class="sku1"[^>]*>\s*<ul>(.*?)</ul>', text, re.S)
    if not m:
        sys.exit('colour picker not found — the page layout may have changed')
    items = [(int(s), html.unescape(re.sub('<[^>]+>', '', lab)).strip())
             for s, lab in re.findall(
                 r'<li[^>]*data-sku1="(\d+)"[^>]*>(.*?)</li>', m.group(1), re.S)]

    files = sorted(set(re.findall(r'\.\./items/1/([^"\']+\.jpg)', text, re.I)))
    best = {}
    for fn in files:
        c = re.search(r'(th\d+)', fn, re.I)
        if not c:
            continue
        code = c.group(1).upper()
        # Frame 00 is the folded product shot — both faces of the cloth against
        # a studio background — not a flat swatch. TH001 is the only colour that
        # has one, and it also has a flat frame; prefer that.
        if code not in best or best[code].startswith('00'):
            best[code] = fn

    out = []
    for sku, code in items:
        if code not in best:
            print(f'  no photograph for {code}')
            continue
        out.append((sku, code, best[code]))
    return out


def crop_caption(im):
    """Drop the seller's caption bar off the bottom of a swatch photo."""
    w, h = im.size
    return im.crop((0, 0, w, int(h * KEEP)))


def fetch():
    text = get(PAGE)
    SNAPSHOT.write_text(text, encoding='utf-8')
    rows = parse_page(text)
    print(f'snapshot: {len(rows)} colours -> {SNAPSHOT.relative_to(ROOT)}')

    IMAGES.mkdir(exist_ok=True)
    IMAGES_LARGE.mkdir(exist_ok=True)
    for _, code, fn in rows:
        large = IMAGES_LARGE / f'{code}.jpg'
        small = IMAGES / f'{code}.jpg'
        if large.exists() and small.exists():
            continue
        raw = large.with_suffix('.tmp')
        raw.write_bytes(get(ITEM_BASE + fn, binary=True))
        im = crop_caption(Image.open(raw).convert('RGB'))
        im.save(large, 'JPEG', quality=92, optimize=True)
        s = im.copy()
        s.thumbnail((SMALL_EDGE, SMALL_EDGE), Image.LANCZOS)
        s.save(small, 'JPEG', quality=92, optimize=True)
        raw.unlink()
        print(f'  {code}  {im.size[0]}x{im.size[1]} (caption cropped)')
        time.sleep(0.4)


def sample_color(path):
    """Median of a centre crop — the same measurement LT and LX use."""
    im = Image.open(path).convert('RGB')
    w, h = im.size
    m = 0.2
    im = im.crop((int(w * m), int(h * m), int(w * (1 - m)), int(h * (1 - m))))
    a = np.asarray(im).reshape(-1, 3)
    return [int(v) for v in np.median(a, axis=0).round().astype(int)]


def hexstr(rgb):
    return '#%02x%02x%02x' % tuple(rgb)


def build():
    if not SNAPSHOT.exists():
        sys.exit('no snapshot — run with --fetch first')
    rows = parse_page(SNAPSHOT.read_text(encoding='utf-8'))

    colors = []
    for sku, code, _ in rows:
        large = IMAGES_LARGE / f'{code}.jpg'
        if not large.exists():
            sys.exit(f'missing image {large.name} — run with --fetch')
        rgb = sample_color(large)
        colors.append({
            # No names exist for this line; the code is the identity.
            'name': code,
            'slug': code.lower(),
            'sku': code,
            'code': code,
            'hex': hexstr(rgb),
            'rgb': rgb,
            'nap': None,
            'image': f'images/{code}.jpg',
            'image_large': f'images/large/{code}.jpg',
            'source': f'https://mitokuya.co.jp/shop/detail.html?item_number=1&sku1={sku}',
            'sources': ['mitokuya-lamous-th'],
        })

    colors.sort(key=lambda c: c['code'])

    doc = {
        'meta': {
            'product': 'Lamous®-TH',
            'also_known_as': ['ラムース®-TH'],
            'manufacturer': None,
            'status': 'current',
            'color_count': len(colors),
            'compiled': time.strftime('%Y-%m-%d'),
            'about': (
                'Lamous® is a Japanese suede-like artificial leather, a different '
                'product from Toray’s Ultrasuede. It is here because it is the same '
                'kind of cloth bought for the same kind of work. Read from 美徳屋 '
                '(Mitokuya), a Japanese retailer, whose Lamous®-TH listing carries the '
                'whole grade as a colour picker on one page.'
            ),
            'rebuild': ('python3 scraping/build_lamous_th.py --fetch && '
                        'python3 scraping/build_lamous_th.py'),
            'naming_note': (
                'This line has no colour names. The picker and the cart both identify a '
                'colour by its code alone, so `name` is the code.'
            ),
            'color_note': (
                'hex/rgb are sampled from the retailer’s swatch photographs, not from '
                'official Lamous colour values, and are approximate. Each is the median '
                'of a centre crop — the same measurement used for LT and LX, so the '
                'three products’ values are comparable. The photographs carry a caption '
                'bar with the code printed across the bottom of the frame; it sits at '
                '85-90% of frame height on all 49 and is cropped off on the way in, so '
                'neither the sample nor the tile contains it.'
            ),
            'nap_note': (
                'No nap block. The photographs are about 256px, and about 197px once '
                'the caption bar is cropped — under the 300px minimum nap contrast can '
                'be measured from. Contrast could be modelled instead, but the curve '
                'that models it was fitted on Ultrasuede LT, and using it here would '
                'assert that a different manufacturer’s fabric follows the same '
                'contrast-against-lightness relationship, which nothing here has '
                'measured. So these colours are drawn from their photographs.'
            ),
            'coverage_note': (
                'The page states the grade has 49 colours ("49色取り揃え") and the picker '
                'lists 49, so this is the whole TH range rather than one channel’s '
                'selection.'
            ),
            'specifications': {
                'thickness': '0.58 (±0.05) mm',
                'width': '130cm',
                'roll': '130cm × 30m',
                'composition': 'Polyester 92%, Polyurethane 8%',
                'origin': 'Made in Japan',
                'source': PAGE,
            },
            'not_recorded': [
                'manufacturer — the listing names no company, only "Made in Japan"',
                'weight',
            ],
        },
        'sources': [
            {'id': 'mitokuya-lamous-th', 'url': PAGE,
             'note': ('retailer catalogue page; the colour picker carries the whole '
                      'grade. Snapshotted in scraping/lamous_th_page.html')},
        ],
        'colors': colors,
    }

    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + '\n')
    print(f'wrote {OUT.relative_to(ROOT)}: {len(colors)} colours')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--fetch', action='store_true',
                    help='snapshot the page and download swatch photographs')
    a = ap.parse_args()
    fetch() if a.fetch else build()
