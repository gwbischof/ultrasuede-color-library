#!/usr/bin/env python3
"""Build ../texvision-ds102.json — the Korean faux suede sold as Texvision DS102.

Not an Ultrasuede product and not a Japanese one: a Korean PU-impregnated
polyester microfibre suede, 0.6mm, sold on eBay by "What More Fabric" of Seoul.
The listing's own Item Specifics give Brand "Texvision" and MPN "0.6T DS102",
which is where the product name here comes from — see meta.identity_note for how
much weight that deserves.

    python3 scraping/build_texvision_ds102.py --fetch   # download swatch photos
    python3 scraping/build_texvision_ds102.py           # sample, write the JSON

This is the least precise dataset in the library, and the reasons are worth
stating rather than burying:

  * **The photographs are styled drapes, not swatches.** Every other product
    here is shot flat; these are swirled and folded under studio light, so a
    centre crop would land on whatever fold happens to be at the centre. The
    colour is therefore the median over every fabric pixel in the frame, which
    sits at the middle of the illumination spread instead of at an arbitrary
    point in it.

  * **How far off that is, is measured, not guessed.** The listing also carries
    labelled 3x3 charts, and one covers colours 10-18. Sampling those cells and
    comparing gives a mean RGB distance of 25 and a worst case of 45, with
    luminance ratios between 0.90 and 1.18. So treat these as roughly +/-10% in
    luminance. That is worse than the rest of the library and better than
    nothing; MEASURED_AGAINST_CHART records the comparison.

  * **No nap block.** What varies across one of these frames is folds, not nap,
    so there is no nap here to measure even though the images are large enough.

eBay returns 403 to scripted fetches of the listing page, so the variation list
(name, stock flag, image id per colour) was captured from a browser session and
is committed as scraping/texvision_ds102_variations.json. The images themselves
come off eBay's CDN, which does answer, so --fetch still works unattended.
"""

import argparse
import json
import pathlib
import sys
import time
import urllib.request

import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
VARIATIONS = ROOT / 'scraping' / 'texvision_ds102_variations.json'
IMAGES = ROOT / 'images'
IMAGES_LARGE = IMAGES / 'large'
OUT = ROOT / 'texvision-ds102.json'

LISTING = 'https://www.ebay.com/itm/223986181465'
LARGE_EDGE = 600
SMALL_EDGE = 100
PREFIX = 'ds102'

# Colour 10-18 as read off the seller's own labelled chart (image
# ZOUAAOSwBlFeoLCS, upper band of each 3x3 cell, clear of the badge and the
# printed name), against the same colours read off their drape photographs.
# Kept so the claim in the docstring can be re-checked rather than trusted.
MEASURED_AGAINST_CHART = {
    'chart_image': 'https://i.ebayimg.com/images/g/ZOUAAOSwBlFeoLCS/s-l1600.jpg',
    'colors_compared': list(range(10, 19)),
    'mean_rgb_distance': 25,
    'max_rgb_distance': 45,
    'luminance_ratio_range': [0.90, 1.18],
}

UA = 'ultrasuede-color-library/1.0 (+https://github.com/gwbischof/ultrasuede-color-library)'


def rows():
    if not VARIATIONS.exists():
        sys.exit(f'missing {VARIATIONS.name}')
    return json.load(VARIATIONS.open())['colors']


def fetch():
    IMAGES.mkdir(exist_ok=True)
    IMAGES_LARGE.mkdir(exist_ok=True)
    for n, name, _oos, size, iid in rows():
        large = IMAGES_LARGE / f'{PREFIX}-{n:02d}.jpg'
        small = IMAGES / f'{PREFIX}-{n:02d}.jpg'
        if large.exists() and small.exists():
            continue
        url = f'https://i.ebayimg.com/00/s/{size}/z/{iid}/$_57.JPG'
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=60) as r:
            large.write_bytes(r.read())
        im = Image.open(large).convert('RGB')
        im.thumbnail((LARGE_EDGE, LARGE_EDGE), Image.LANCZOS)
        im.save(large, 'JPEG', quality=92, optimize=True)
        s = im.copy()
        s.thumbnail((SMALL_EDGE, SMALL_EDGE), Image.LANCZOS)
        s.save(small, 'JPEG', quality=92, optimize=True)
        print(f'  {n:02d} {name}')
        time.sleep(0.3)


def drape_color(path):
    """Median over the fabric pixels of a draped-fabric photograph.

    Deliberately not a centre crop — see the module docstring.

    The background mask is tight on purpose: only pixels that are both very
    bright (min channel > 245) and nearly neutral (spread < 8) count as studio
    paper. A looser rule eats the pale fabrics themselves — at min > 225 it
    masked 59% of Light Gray's frame and 26% of Ivory's, and dragged both
    towards their own shadows.
    """
    a = np.asarray(Image.open(path).convert('RGB')).astype(float).reshape(-1, 3)
    mx, mn = a.max(1), a.min(1)
    bg = (mn > 245) & ((mx - mn) < 8)
    keep = a[~bg]
    if len(keep) < 1000:           # an almost-white fabric: keep everything
        keep = a
    return [int(v) for v in np.median(keep, axis=0).round().astype(int)]


def build():
    colors = []
    for n, name, oos, _size, _iid in rows():
        large = IMAGES_LARGE / f'{PREFIX}-{n:02d}.jpg'
        if not large.exists():
            sys.exit(f'missing {large.name} — run with --fetch')
        rgb = drape_color(large)
        colors.append({
            'name': name,
            'slug': ''.join(c if c.isalnum() else '-' for c in name.lower()).strip('-'),
            'sku': f'DS102-{n:02d}',
            'code': f'{n:02d}',
            'hex': '#%02x%02x%02x' % tuple(rgb),
            'rgb': rgb,
            'nap': None,
            'image': f'images/{PREFIX}-{n:02d}.jpg',
            'image_large': f'images/large/{PREFIX}-{n:02d}.jpg',
            'in_stock': not oos,
            'source': LISTING,
            'sources': ['ebay-whatmorefabric-ds102'],
        })

    doc = {
        'meta': {
            'product': 'Texvision DS102 (0.6mm)',
            'also_known_as': ['Korean faux suede'],
            'manufacturer': None,
            'status': 'current',
            'color_count': len(colors),
            'compiled': time.strftime('%Y-%m-%d'),
            'about': (
                'A Korean PU-impregnated polyester microfibre suede, sold on eBay by '
                '"What More Fabric" of Seoul. Not an Ultrasuede product — the listing '
                'title uses the word generically — and not related to the Japanese '
                'products here beyond being the same kind of cloth.'
            ),
            'rebuild': ('python3 scraping/build_texvision_ds102.py --fetch && '
                        'python3 scraping/build_texvision_ds102.py'),
            'identity_note': (
                'Brand "Texvision" and MPN "0.6T DS102" are the listing’s own Item '
                'Specifics, filled in by the seller. Texvision appears to be a Seoul '
                'textile company, but nothing found establishes whether it is the mill '
                'that makes this cloth or a trading name the seller buys under, so '
                'manufacturer is left null rather than asserted.'
            ),
            'naming_note': (
                'Colour names are the seller’s, and several are Pantone fashion-colour '
                'names (Castlerock, Blue Nights, Mood Indigo, Moonstruck, Wild Lime), '
                'which suggests they were assigned at resale rather than by the mill. '
                'The code is the seller’s position in their own list, 1 to 41 — it is '
                'NOT a manufacturer colour number, and it would change if they '
                'reordered the list. Do not treat it as stable identity the way LX’s '
                'CD8 or Lamous’s TH001 can be treated.'
            ),
            'color_note': (
                'The least precise dataset here. The photographs are styled drapes '
                'rather than flat swatches, so hex/rgb is the median over every fabric '
                'pixel in the frame — the middle of the illumination spread — instead '
                'of the centre-crop median the other products use, which on a swirl '
                'would return whatever fold sits at the centre. Checked against the '
                'seller’s own labelled chart for colours 10-18: mean RGB distance 25, '
                'worst 45, luminance ratios 0.90 to 1.18. Treat these as roughly '
                '+/-10% in luminance and do not compare them closely with the '
                'flat-shot products.'
            ),
            'measured_against_chart': MEASURED_AGAINST_CHART,
            'nap_note': (
                'No nap block. What varies across one of these frames is folds, not '
                'nap, so there is nothing here to measure however large the image is.'
            ),
            'coverage_note': (
                'This listing offers 41 colours. The seller’s own sample-set option on '
                'the same listing is captioned "Sample set 2026 ver (122 colors)", so '
                'the full range is around 122 and this is roughly a third of it. The '
                'rest would have to come from their other listings.'
            ),
            'specifications': {
                'thickness': '0.6mm',
                'width': '54 inch',
                'fiber_content': 'PET (Polyester) 90%, PU 10% after dissolving',
                'weight': '300g per yard / 240 GSM',
                'origin': 'South Korea',
                'source': LISTING,
            },
            'not_recorded': ['manufacturer — see identity_note'],
        },
        'sources': [
            {'id': 'ebay-whatmorefabric-ds102', 'url': LISTING,
             'note': ('eBay listing; variation list captured from a browser session '
                      'and committed as scraping/texvision_ds102_variations.json, '
                      'because eBay 403s scripted fetches of the page')},
        ],
        'colors': colors,
    }
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + '\n')
    print(f'wrote {OUT.relative_to(ROOT)}: {len(colors)} colours')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--fetch', action='store_true')
    a = ap.parse_args()
    fetch() if a.fetch else build()
