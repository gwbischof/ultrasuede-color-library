#!/usr/bin/env python3
"""Build ../st.json from Toray's live Ultrasuede® ST swatch site.

ST is still current, and swatches.ultrasuede.us still serves it — the same site
LT's 36 were reconstructed from, which now offers only ST and HP. So this reads
the live page rather than the archive.

    python3 scraping/build_st.py --fetch    # snapshot page + swatch photos
    python3 scraping/build_st.py            # sample colours, write ../st.json

Of the products here this is the one closest to LT: same manufacturer, same
style-and-colour-number scheme (8023-5597), swatch photographs shot the same
way, and enlarged views at 418px — the same size LT's own large captures are.
That last point matters: 418 clears build_dataset's NAP_MEASURABLE of 300, so
ST contrast is measured rather than modelled, and an ST shader and an LT shader
are the same kind of picture.

The page markup is NOT the one build_dataset's SWATCH_RE parses. That regex was
written for the archived captures, which wrapped a swatch in <span>…</em>; the
live site emits a structured <li> with swatchesNumber / swatchesTitle, so it
gets its own parser here rather than a regex that has to satisfy both.
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

# Shared with LT rather than reimplemented, so the two products' hexes and
# shaders mean the same thing. build_dataset guards its entry point.
from build_dataset import nap

ROOT = pathlib.Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / 'scraping' / 'st_page.html'
IMAGES = ROOT / 'images'
IMAGES_LARGE = IMAGES / 'large'
OUT = ROOT / 'st.json'

SITE = 'https://swatches.ultrasuede.us'
PAGE = f'{SITE}/swatches/search_result.php?product=ST'
LARGE_URL = f'{SITE}/swatches/images_enlarged_view/'
SMALL_EDGE = 100

ITEM_RE = re.compile(
    r'<li>\s*<p class="swatchesImg">.*?'
    r'<p class="swatchesType">(.*?)</p>\s*'
    r'<p class="swatchesNumber">(.*?)</p>\s*'
    r'<p class="swatchesTitle">(.*?)</p>(.*?)</li>',
    re.S)

UA = 'ultrasuede-color-library/1.0 (+https://github.com/gwbischof/ultrasuede-color-library)'


def get(url, binary=False):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = r.read()
    return d if binary else d.decode('utf-8', 'replace')


def parse_page(text):
    """[(sku, style, code, name, orderable)] from the live swatch list."""
    out = []
    for kind, sku, name, rest in ITEM_RE.findall(text):
        sku = sku.strip()
        if '-' not in sku:
            continue
        style, code = sku.split('-', 1)
        out.append({
            'sku': sku,
            'style': style,
            'code': code,
            'name': html.unescape(re.sub('<[^>]+>', '', name)).strip(),
            'kind': kind.strip(),
            # the Request button is a sample_request link; no link, not orderable
            'orderable': 'addsku' in rest,
        })
    if not out:
        sys.exit('no swatches parsed — the page markup may have changed')
    return out


def fetch():
    text = get(PAGE)
    SNAPSHOT.write_text(text, encoding='utf-8')
    rows = parse_page(text)
    print(f'snapshot: {len(rows)} colours -> {SNAPSHOT.relative_to(ROOT)}')

    IMAGES.mkdir(exist_ok=True)
    IMAGES_LARGE.mkdir(exist_ok=True)
    for r in rows:
        large = IMAGES_LARGE / f"{r['sku']}.jpg"
        small = IMAGES / f"{r['sku']}.jpg"
        if large.exists() and small.exists():
            continue
        large.write_bytes(get(LARGE_URL + r['sku'] + '.jpg', binary=True))
        im = Image.open(large).convert('RGB')
        s = im.copy()
        s.thumbnail((SMALL_EDGE, SMALL_EDGE), Image.LANCZOS)
        s.save(small, 'JPEG', quality=92, optimize=True)
        print(f"  {r['sku']}  {im.size[0]}x{im.size[1]}  {r['name']}")
        time.sleep(0.5)


def sample_color(path):
    """Median of a centre crop — identical to build_dataset's sample_color."""
    im = Image.open(path).convert('RGB')
    w, h = im.size
    m = 0.2
    im = im.crop((int(w * m), int(h * m), int(w * (1 - m)), int(h * (1 - m))))
    a = np.asarray(im).reshape(-1, 3)
    return [int(v) for v in np.median(a, axis=0).round().astype(int)]


def build():
    if not SNAPSHOT.exists():
        sys.exit('no snapshot — run with --fetch first')
    rows = parse_page(SNAPSHOT.read_text(encoding='utf-8'))

    colors = []
    for r in rows:
        large = IMAGES_LARGE / f"{r['sku']}.jpg"
        if not large.exists():
            sys.exit(f"missing image {large.name} — run with --fetch")
        rgb = sample_color(large)
        colors.append({
            'name': r['name'],
            'slug': ''.join(c if c.isalnum() else '-'
                            for c in r['name'].lower()).strip('-'),
            'sku': r['sku'],
            'code': r['code'],
            'hex': '#%02x%02x%02x' % tuple(rgb),
            'rgb': rgb,
            # corners=False: Toray's frames are edge-to-edge fabric, no
            # watermark. 418px clears NAP_MEASURABLE, so contrast is measured.
            'nap': nap(str(large), rgb),
            'image': f"images/{r['sku']}.jpg",
            'image_large': f"images/large/{r['sku']}.jpg",
            'orderable': r['orderable'],
            'source': PAGE,
            'sources': ['swatches-st'],
        })

    colors.sort(key=lambda c: c['code'])
    styles = sorted({r['style'] for r in rows})
    measured = sum(1 for c in colors if c['nap']
                   and c['nap']['contrast_source'] == 'measured')

    doc = {
        'meta': {
            'product': 'Ultrasuede® ST',
            'also_known_as': ['Ultrasuede® Soft'],
            'manufacturer': 'Toray',
            'status': 'current',
            'color_count': len(colors),
            'style_numbers': [
                {'number': s, 'era': 'current',
                 'note': 'from the swatch number on every ST listing'}
                for s in styles
            ],
            'compiled': time.strftime('%Y-%m-%d'),
            'about': (
                'Read from Toray’s own swatch site, swatches.ultrasuede.us — the same '
                'site LT was reconstructed from, which now lists only ST and HP. ST is '
                'still current, so this is the live page rather than the archive.'
            ),
            'rebuild': ('python3 scraping/build_st.py --fetch && '
                        'python3 scraping/build_st.py'),
            'color_note': (
                'hex/rgb are sampled from Toray’s swatch photographs, not official '
                'Toray colour values, and are approximate. Each is the median of a '
                'centre crop — the same measurement used for LT and LX, so the three '
                'are comparable. Enlarged views are 418px, the same size as LT’s large '
                'captures, and the frames are edge-to-edge fabric with no watermark, so '
                'the plain centre crop applies rather than the corner-patch variant.'
            ),
            'nap_note': (
                f'Every colour carries a `nap` block measured the same way as LT’s and '
                f'meaning the same thing. At 418px all {measured} clear the 300px '
                f'minimum, so contrast is measured throughout and none falls back to '
                f'the curve fitted on LT.'
            ),
            'coverage_note': (
                'This is what the swatch site currently lists. Earlier ST ranges were '
                'wider — Field’s catalogues from 2003–2010 print ST colours under 45" '
                'numbers that were later restyled to 58" ones — and none of that history '
                'is here; see research/FINDINGS.md for what is known of it.'
            ),
            'not_recorded': [
                'composition', 'width', 'weight', 'thickness',
                'The swatch listing publishes no specification text.',
            ],
        },
        'sources': [
            {'id': 'swatches-st', 'url': PAGE,
             'note': 'live Toray swatch site; snapshotted in scraping/st_page.html'},
        ],
        'colors': colors,
    }
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + '\n')
    print(f'wrote {OUT.relative_to(ROOT)}: {len(colors)} colours, '
          f'{measured} with measured nap')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--fetch', action='store_true')
    a = ap.parse_args()
    fetch() if a.fetch else build()
