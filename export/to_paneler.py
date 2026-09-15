#!/usr/bin/env python3
"""Export this library as Paneler's fabric catalogue.

    python3 export/to_paneler.py ../Paneler

Writes two things into the Paneler repo and nothing else:

    lib/fabrics/catalog.json      one entry per fabric, grouped by product
    public/fabrics/*.webp         a chip and a shelf-sized swatch for each

It lives here rather than in Paneler because the work is image derivation and
this is the repo with Pillow. Paneler consumes the output and has no dependency
on this repo at runtime — the JSON and the images are vendored, so Paneler
builds with this checkout absent.

Two things it is careful about, both of which would be silent damage:

**Paneler's own LX values win.** Fourteen LX colours already exist in Paneler
with hexes tuned by eye against the real cloth — 1.32x to 2.12x their raw photo
value, because a suede's micro-shadows read darker in a photograph than the
fabric does in hand. This library stores the raw measurement. Importing over
those would undo the tuning, so they are read out of Paneler's own
defaultPalettes.ts and passed through untouched, matched to their library entry
by colour code.

**Their ids are frozen.** `lx-red`, `lx-white` and the rest are written into
saved designs and into stored fabric lists, so they keep the ids they have, not
`lx-gf2`. Everything new gets `<line>-<code>`.

Everything else takes the documented lift (two x1.15 passes, x1.3225) on the way
in. That is an assertion rather than a measurement — the micro-shadow effect is
a property of suede rather than of one camera, so it should carry across, but
nothing here has checked it against the physical cloth for any product but LX.
`lifted: true` on each entry records which values it was applied to.
"""

import json
import pathlib
import re
import shutil
import sys

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Products in the order Paneler should present them: what Garrett sews with
# first, then the rest, then the discontinued line.
# Products whose swatch comes from the SHADER rather than the photograph.
# Their photographs are unusable as colour chips and no crop rescues them:
# LT's custom colours carry a "Field's Fabrics" watermark stamped across the
# middle, DS102's carry a numbered badge and the colour name printed into the
# frame over draped cloth, and Shammy's are 93px cells off a printed card with
# its cell edge in shot. The renders come from images/rendered/, drawn by the
# real nap.js in headless Chrome — see export/render_swatches.py.
#
# LX and ST keep their photographs: theirs are clean 400-800px frames from
# Toray, and they beat what the shader draws.
FROM_SHADER = {'lt', 'ds102', 'sham'}
RENDERED = ROOT / 'images' / 'rendered'

PRODUCTS = [
    ('lx.json', 'Ultrasuede LX', 'lx'),
    ('st.json', 'Ultrasuede ST', 'st'),
    ('lamous-th.json', 'Lamous TH', 'lam'),
    ('shammy.json', 'Shammy 707J', 'sham'),
    ('texvision-ds102.json', 'Korean DS102', 'ds102'),
    ('lt.json', 'Ultrasuede LT', 'lt'),
]
# Sections to take from each file. `patterns` are prints, not flat colours, and
# `historical_colors` have no hex at all.
SECTIONS = ('colors', 'custom_colors')

# The documented lift, as defaultPalettes.ts describes it.
LIFT = 1.15 * 1.15

# Paneler's fourteen existing LX ids, against the library colour code each one
# is. Written out rather than matched on name so a renamed colour upstream
# cannot silently re-point an id that is already in saved designs.
LX_EXISTING = {
    'CD8': 'lx-white', 'CA5': 'lx-ivory', 'GB2': 'lx-black',
    'CC9': 'lx-citron', 'CT6': 'lx-orange', 'GF2': 'lx-red',
    'WA6': 'lx-rose', 'WA4': 'lx-burgundy', 'GH5': 'lx-purple',
    'CC6': 'lx-sky', 'WA7': 'lx-blue', 'CT5': 'lx-turquoise',
    'GV9': 'lx-forest-green', 'GD8': 'lx-brownstone',
}

# Chip in the palette is 28 CSS px, so 96 covers 3x. The profile page's shelf
# strip is about 86x176 CSS px, so its long edge wants ~530 at 3x — capped at
# 512, and only emitted where the source actually has the pixels, rather than
# upscaling a 93px Shammy cell into a file that pretends otherwise.
CHIP_PX = 96
SHELF_PX = 512
SHELF_MIN_SOURCE = 240


def lift(hex_str):
    r, g, b = (int(hex_str[i:i + 2], 16) for i in (1, 3, 5))
    return '#%02x%02x%02x' % tuple(min(255, round(v * LIFT)) for v in (r, g, b))


def paneler_lx(paneler):
    """{lx-id: hex} as Paneler currently ships them — the tuned values."""
    src = (paneler / 'lib' / 'defaultPalettes.ts').read_text()
    return dict(re.findall(r'\{ id: "(lx-[^"]+)", label: "[^"]*", color: "(#[0-9a-f]{6})"',
                           src, re.I))


def emit_images(entry, out_dir, slug, rendered_key=None):
    """Chip and, where the source is big enough, a shelf-sized copy."""
    paths = {}
    if rendered_key:
        p = RENDERED / f'{rendered_key}.webp'
        if not p.exists():
            sys.exit(f'missing render {p.name} — run export/render_swatches.py')
    else:
        src = entry.get('image_large') or entry.get('image')
        if not src:
            return paths
        p = ROOT / src
        if not p.exists():
            return paths
    im = Image.open(p).convert('RGB')

    chip = im.copy()
    chip.thumbnail((CHIP_PX, CHIP_PX), Image.LANCZOS)
    chip.save(out_dir / f'{slug}.webp', 'WEBP', quality=88, method=6)
    paths['swatch'] = f'/fabrics/{slug}.webp'

    if min(im.size) >= SHELF_MIN_SOURCE:
        shelf = im.copy()
        shelf.thumbnail((SHELF_PX, SHELF_PX), Image.LANCZOS)
        shelf.save(out_dir / f'{slug}@large.webp', 'WEBP', quality=88, method=6)
        paths['swatchLarge'] = f'/fabrics/{slug}@large.webp'
    return paths


def main(paneler):
    out_json = paneler / 'lib' / 'fabrics' / 'catalog.json'
    out_img = paneler / 'public' / 'fabrics'
    out_json.parent.mkdir(parents=True, exist_ok=True)
    if out_img.exists():
        shutil.rmtree(out_img)
    out_img.mkdir(parents=True)

    tuned = paneler_lx(paneler)
    groups, kept_ids, n_lifted = [], set(), 0

    for fname, label, prefix in PRODUCTS:
        doc = json.loads((ROOT / fname).read_text())
        entries = []
        for section in SECTIONS:
            for c in doc.get(section) or []:
                if not c.get('hex') or not c.get('code'):
                    continue
                code = str(c['code'])
                existing = LX_EXISTING.get(code) if prefix == 'lx' else None
                if existing and existing in tuned:
                    fid, color, lifted = existing, tuned[existing], False
                else:
                    fid = f'{prefix}-{code.lower()}'
                    color, lifted = lift(c['hex']), True
                    n_lifted += 1
                if fid in kept_ids:
                    sys.exit(f'duplicate fabric id {fid}')
                kept_ids.add(fid)
                e = {'id': fid, 'label': c['name'], 'color': color}
                if lifted:
                    e['lifted'] = True
                if prefix in FROM_SHADER:
                    # the swatch is drawn, not photographed
                    e['drawn'] = True
                rk = (f"{fname.replace('.json', '')}-{c['code']}"
                      if prefix in FROM_SHADER else None)
                e.update(emit_images(c, out_img, fid, rk))
                entries.append(e)
        if entries:
            groups.append({'label': label, 'entries': entries})
            print(f'  {label:<18}{len(entries):>4} fabrics')

    out_json.write_text(json.dumps({
        '_generated': 'export/to_paneler.py in gwbischof/ultrasuede-color-library',
        '_note': (
            'Hexes are sampled from swatch photographs and are approximate. '
            'Entries marked `lifted` carry the documented two-x1.15 brightness '
            'correction, because a suede photographs darker than it reads in '
            'hand; the LX entries without it are hand-tuned against the real '
            'cloth and were passed through untouched. Do not regenerate those '
            'from the library or the tuning is lost.'
        ),
        'groups': groups,
    }, indent=1, ensure_ascii=False) + '\n')

    shaded = sum(1 for g in groups for e in g['entries'] if e.get('drawn'))
    total = sum(len(g['entries']) for g in groups)
    size = sum(f.stat().st_size for f in out_img.iterdir())
    print(f'\n  {total} fabrics in {len(groups)} groups '
          f'({n_lifted} lifted, {total - n_lifted} passed through)')
    print(f'  {len(list(out_img.iterdir()))} images, {size/1024/1024:.1f} MB')
    print(f'  {shaded} swatches drawn from the shader, '
          f'{total - shaded} photographed')
    print(f'  -> {out_json.relative_to(paneler)}')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(pathlib.Path(sys.argv[1]).resolve())
