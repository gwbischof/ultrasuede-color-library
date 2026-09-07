#!/usr/bin/env python3
"""Independent check of ../lt.json against the archived captures and images.

Deliberately re-derives its facts from snapshots/ rather than reusing
build_dataset.py's helpers, so a bug in the builder shows up as a mismatch.

    python3 verify.py           # offline structural checks
    python3 verify.py --links   # also HEAD every distinct archive URL
"""

import glob
import html
import json
import os
import re
import statistics
import subprocess
import time
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

fails = []
checks = 0


def iso(ts):
    return f'{ts[0:4]}-{ts[4:6]}-{ts[6:8]}'


def corner_boxes(size, inset, box):
    """The four sampling patches, as crop boxes. Written out again here rather
    than imported, so a change to the builder's geometry shows up as a hex that
    no longer reproduces instead of as two files agreeing with each other."""
    w, h = size
    iw, ih, sw, sh = int(w * inset), int(h * inset), int(w * box), int(h * box)
    return [(iw, ih, iw + sw, ih + sh), (w - iw - sw, ih, w - iw, ih + sh),
            (iw, h - ih - sh, iw + sw, h - ih),
            (w - iw - sw, h - ih - sh, w - iw, h - ih)]


def channels(im):
    """An image's three channels as flat byte strings."""
    raw = im.convert('RGB').tobytes()
    return [raw[i::3] for i in range(3)]


def corner_median(path, inset, box):
    """Per-channel median over those four patches — the recovered colours' hex."""
    im = Image.open(path)
    px = [[], [], []]
    for b in corner_boxes(im.size, inset, box):
        for i, ch in enumerate(channels(im.crop(b))):
            px[i] += ch
    return [round(statistics.median(c)) for c in px]


def paper_free(path, limit=24):
    """True when no corner of a cropped scan disagrees with the rest of it.

    The failure this is here to catch is scanner paper left in the frame:
    #2608's crop once reached ninety columns past the cloth to take in a dark
    strip at the edge of the scan, and the white wedge that came with it sat in
    a corner, which is exactly where the colour is read from.
    """
    im = Image.open(path)

    def median_luma(part):
        r, g, b = channels(part)
        return statistics.median(0.2126 * x + 0.7152 * y + 0.0722 * z
                                 for x, y, z in zip(r, g, b))

    whole = median_luma(im)
    return all(abs(median_luma(im.crop(b)) - whole) <= limit
               for b in corner_boxes(im.size, 0.06, 0.16))


def check(cond, msg):
    global checks
    checks += 1
    if not cond:
        fails.append(msg)
    # returned so a caller can skip follow-up checks that would only fail again
    return cond


def main():
    data = json.load(open(os.path.join(ROOT, 'lt.json'), encoding='utf-8'))
    colors, patterns = data['colors'], data['patterns']
    src_ids = {s['id'] for s in data['sources']}

    # --- colours re-derived straight from the newest populated capture ------
    newest = os.path.join(HERE, 'snapshots/LT/20240805162934.html')
    t = open(newest, encoding='utf-8', errors='replace').read()
    truth = {}
    for m in re.finditer(
            r'title="&lt;em&gt;LT (\d{4}-\d{4})&lt;/em&gt; ([^"]*)"', t):
        truth[m.group(1)] = html.unescape(m.group(2)).strip()
    check(len(truth) == 36, f'expected 36 colours in newest capture, got {len(truth)}')
    check(int(re.search(r'\((\d+) items found\)', t).group(1)) == 36,
          'newest capture header does not say 36 items')

    check(len(colors) == 36, f'lt.json has {len(colors)} colours, expected 36')
    for c in colors:
        check(c['sku'] in truth, f'{c["sku"]} not in the newest capture')
        if c['sku'] in truth:
            check(truth[c['sku']] == c['name'],
                  f'{c["sku"]} name mismatch: {c["name"]!r} vs {truth[c["sku"]]!r}')
        check(c['sku'] == f'8801-{c["code"]}', f'{c["sku"]} sku/code disagree')
        check(re.fullmatch(r'#[0-9a-f]{6}', c['hex']), f'{c["sku"]} bad hex {c["hex"]}')
        check('#%02x%02x%02x' % tuple(c['rgb']) == c['hex'], f'{c["sku"]} rgb/hex disagree')
        check(c['source'].startswith('https://web.archive.org/web/'),
              f'{c["sku"]} source is not an archive URL')
        check(bool(c['sources']), f'{c["sku"]} has no sources')
        for sid in c['sources']:
            check(sid in src_ids, f'{c["sku"]} references unknown source {sid}')

        for key in ('image', 'image_large'):
            rel = c[key]
            if rel is None:
                continue
            p = os.path.join(ROOT, rel)
            check(os.path.exists(p), f'{c["sku"]} missing {rel}')
            if os.path.exists(p):
                check(open(p, 'rb').read(2) == b'\xff\xd8', f'{rel} is not a JPEG')

    check(len({c['sku'] for c in colors}) == 36, 'duplicate SKUs')
    check(len({c['slug'] for c in colors}) == 36, 'duplicate slugs')

    # --- the central claim: every populated capture shows the same 36 -------
    caps = sorted(os.listdir(os.path.join(HERE, 'snapshots/LT')))
    populated = 0
    for fn in caps:
        raw = open(os.path.join(HERE, 'snapshots/LT', fn),
                   encoding='utf-8', errors='replace').read()
        skus = set(re.findall(r'images/(\d{4}-\d{4})\.jpg" alt=""', raw))
        if not skus:
            continue
        populated += 1
        check(skus == set(truth),
              f'{fn}: colour set differs from the 2024 capture')
    check(populated == 21, f'expected 21 populated captures, found {populated}')

    # --- patterns -----------------------------------------------------------
    # re-read every Light Jungle capture with an independent regex over the
    # de-tagged text, so a bug in build_dataset's parser shows up here.
    jung = {}
    for fn in sorted(os.listdir(os.path.join(HERE, 'snapshots/hist'))):
        if 'jungle' not in fn.lower() or not fn.endswith('.html'):
            continue
        raw = open(os.path.join(HERE, 'snapshots/hist', fn),
                   encoding='utf-8', errors='replace').read()
        flat = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', raw)))
        rows = re.findall(
            r'([A-Z][A-Za-z ]{1,20}?)(\*?) ?Pattern: ?(\d{3}) Color: ?(\d{3})', flat)
        check(len(rows) == 17, f'{fn}: found {len(rows)} patterns, expected 17')
        jung[fn] = {(pat, col): (nm.strip(), star == '*')
                    for nm, star, pat, col in rows}

    check(len(jung) == 8, f'expected 8 jungle captures on disk, found {len(jung)}')
    dates = sorted(re.search(r'(\d{8})', fn).group(1) for fn in jung)
    latest_j, earliest_j = dates[-1], dates[0]
    truth_j = jung[next(f for f in jung if latest_j in f)]
    for fn, rows in jung.items():
        check(set(rows) == set(truth_j), f'{fn}: pattern set differs from the last capture')

    check(len(patterns) == 17, f'{len(patterns)} patterns, expected 17')
    for p in patterns:
        key = (p['pattern'], p['color'])
        check(re.fullmatch(r'\d{3}', p['pattern']), f'{p["name"]} bad pattern number')
        check(re.fullmatch(r'\d{3}', p['color']), f'{p["name"]} bad colour number')
        check(key in truth_j, f'{p["name"]} {key} not in the last jungle capture')
        if key in truth_j:
            name, star = truth_j[key]
            check(name == p['name'], f'{key} name mismatch: {p["name"]!r} vs {name!r}')
            check(p['stock'] == ('in stock' if star else 'special order'),
                  f'{p["name"]} {key} stock disagrees with the capture')
        check(p['first_listed'] == iso(earliest_j), f'{p["name"]} bad first_listed')
        check(p['last_listed'] == iso(latest_j), f'{p["name"]} bad last_listed')
        check(p['last_year_listed'] == int(latest_j[:4]),
              f'{p["name"]} last_year_listed {p["last_year_listed"]}')
        check(p['source'].startswith('https://web.archive.org/web/' + latest_j),
              f'{p["name"]} source is not the latest jungle capture')
        for sid in p['sources']:
            check(sid in src_ids, f'{p["name"]} references unknown source {sid}')

        # in_stock_until: set only where the asterisk was present at some point
        # and gone by the final capture.
        hist = [(d, jung[next(f for f in jung if d in f)].get(key))
                for d in dates]
        hist = [(d, v) for d, v in hist if v]
        had = [d for d, v in hist if v[1]]
        want = iso(had[-1]) if had and not hist[-1][1][1] else None
        check(p['in_stock_until'] == want,
              f'{p["name"]} in_stock_until {p["in_stock_until"]}, expected {want}')

        if p['image']:
            fp = os.path.join(ROOT, p['image'])
            check(os.path.exists(fp), f'{p["name"]} missing {p["image"]}')
            check(p['image'].endswith(p['color'] + '.jpg'),
                  f'{p["name"]} image does not match colour {p["color"]}')

    jm = data['meta']['light_jungle']
    check(jm['pattern_count'] == 17, 'meta.light_jungle.pattern_count')
    check(jm['first_official_listing'] == iso(earliest_j),
          'meta.light_jungle.first_official_listing')
    check(jm['last_official_listing'] == iso(latest_j),
          'meta.light_jungle.last_official_listing')
    # the delisting claim: no Light Jungle in the 2010 product menu.
    menu = open(os.path.join(HERE, 'snapshots/hist',
                             'uscom_searchresult_Light_20101201.html'),
                encoding='utf-8', errors='replace').read()
    sel = re.search(r'(?is)<select[^>]*name="?product.*?</select>', menu).group(0)
    opts = re.findall(r'(?i)<option value="([^"]*)"', sel)
    check('Light Jungle' not in opts, '2010 product menu still lists Light Jungle')
    check('Ambiance Jungle' in opts, '2010 product menu has no Ambiance Jungle')
    check('Light' in opts, '2010 product menu has no Light')

    # --- Field's Fabrics custom colours -------------------------------------
    custom = data['custom_colors']
    check('fields_unverified' not in data,
          'fields_unverified survives; it was folded into custom_colors')
    # Two populations under one heading, and they cannot be checked the same
    # way. The shop-era colours come off Field's own product pages and can be
    # asked for a product URL, a listing history and an exclusivity claim. The
    # recovered ones come off the pre-2011 list pages, have none of those, and
    # are checked further down with the rest of that record.
    recovered = [e for e in custom
                 if e['custom_basis'] == 'predates_official_record']
    shop = [e for e in custom
            if e['custom_basis'] != 'predates_official_record']
    check(len(shop) == 14, f'{len(shop)} shop-era custom colours, expected 14')
    # 47 off archived captures of Field's own /swatches/ folder, and nine more
    # off the copies still sitting on their live site — two of which are the
    # colour in another weight, and say so in based_on.
    check(len(recovered) == 56, f'{len(recovered)} recovered colours, expected 56')
    off_codes = {c['code'] for c in colors}
    off_names = {c['name'].lower() for c in colors}

    # the no-overlap rule, checked from three directions
    for e in custom:
        check(e['code'] not in off_codes,
              f'custom {e["name"]} ({e["code"]}) collides with an official colour')
        check(e['name'].lower() not in off_names,
              f'custom {e["name"]} shares a name with an official colour')
    check(len({e['code'] for e in custom}) == len(custom), 'duplicate custom codes')
    check(len({e['slug'] for e in custom}) == len(custom), 'duplicate custom slugs')

    # re-read Field's captures independently of the builder
    fdir = os.path.join(HERE, 'snapshots/fields')
    cat = {}       # date -> {code: label} for the custom category
    for fn in sorted(glob.glob(os.path.join(fdir, 'ltcustom_*.html'))):
        raw = open(fn, encoding='utf-8', errors='replace').read()
        if not raw.strip():
            continue
        flat = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', raw)))
        found = dict(re.findall(
            r'#?\s*(\d{4})\s+([A-Z][A-Za-z ]{2,24}?)\s*-*\s*(?:Custom|Premium|Fabric)',
            flat))
        ts = re.search(r'(\d{14})', fn).group(1)
        cat[iso(ts)] = found
    check(len(cat) == 10, f'expected 10 populated custom-category captures, got {len(cat)}')
    # the category held a stable nine items until it dropped to six in 2024
    for d, v in sorted(cat.items()):
        check(len(v) == (6 if d >= '2024' else 9),
              f'custom category {d}: {len(v)} items, expected {6 if d >= "2024" else 9}')
    seen_cat = {c for v in cat.values() for c in v}
    check(seen_cat, 'no codes parsed out of the custom-category captures')
    # every code the category ever showed is either custom or a known official one
    for c in seen_cat:
        check(c in {e['code'] for e in custom} or c in off_codes,
              f'category code {c} landed in neither custom_colors nor colors')
    # and the ones the builder excluded really are official
    for c in data['meta']['fields_custom']['excluded_as_official']:
        check(c in off_codes, f'excluded code {c} is not actually official')
        check(c in seen_cat or c in off_codes, f'excluded code {c} unexplained')

    exclusivity = re.compile(
        r"(?i)(premium|custom)\s+colou?r\s+only\s+available\s+at\s+Field'?s\s+Fabrics")
    for e in custom:
        # every Field's colour number is four digits except LT Blue, #100 —
        # and #7369S Aqua 58, where the S is Field's own mark for the 58" cut
        # of a colour they also listed at 45" (#7369).
        check(re.fullmatch(r'\d{3,4}[A-Z]?', e['code']), f'{e["name"]} bad code')
        check(e['sku'] is None, f'{e["name"]} should have no Toray SKU')
        if e['image']:
            fp = os.path.join(ROOT, e['image'])
            check(os.path.exists(fp), f'{e["name"]} missing {e["image"]}')
            check(open(fp, 'rb').read(2) == b'\xff\xd8', f'{e["image"]} is not a JPEG')
            check(re.fullmatch(r'#[0-9a-f]{6}', e['hex'] or ''), f'{e["name"]} bad hex')
            check('#%02x%02x%02x' % tuple(e['rgb']) == e['hex'],
                  f'{e["name"]} rgb/hex disagree')
        else:
            # a colour with nothing recovered for it has no photograph and so
            # no colour either. The six known only from a ~100px thumbnail sat
            # here until that thumbnail was published, squared, alongside the
            # full scans; nothing is left on this side.
            check(e['hex'] is None, f'{e["name"]} has a hex but no image')
        for sid in e['sources']:
            check(sid in src_ids, f'{e["name"]} references unknown source {sid}')
        check(e['source'].startswith('https://web.archive.org/web/'),
              f'{e["name"]} source is not an archive URL')
        if e['last_listed']:
            check(e['last_year_listed'] == int(e['last_listed'][:4]),
                  f'{e["name"]} last_year_listed disagrees with last_listed')
            check(e['first_listed'] <= e['last_listed'], f'{e["name"]} dates reversed')
        else:
            check(e['last_year_listed'] is None,
                  f'{e["name"]} has a year but no last_listed')

    for e in shop:
        if e['first_listed']:
            check(e['earliest_evidence'] <= e['first_listed'],
                  f'{e["name"]} earliest_evidence after first_listed')
        # the exclusivity claim must be quoted verbatim from a saved capture
        if e['exclusivity_evidence']:
            hits = [p for p in glob.glob(os.path.join(fdir, 'products', '*.html'))
                    if os.path.basename(p).startswith(e['code'])]
            ok = False
            for p in hits:
                raw = open(p, encoding='utf-8', errors='replace').read()
                flat = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', raw)))
                if exclusivity.search(flat):
                    ok = True
            check(ok, f'{e["name"]} claims exclusivity but no capture shows the phrase')
        check(e['exclusive_to'] == "Field's Fabrics",
              f'{e["name"]} is in custom_colors but not marked exclusive')
        # custom_basis must match the evidence actually on the entry
        claimed = bool(e['exclusivity_evidence']) or e['in_custom_category']
        check(e['custom_basis'] == ('fields_exclusivity_claim' if claimed
                                    else 'absent_from_official_line'),
              f'{e["name"]} custom_basis disagrees with its evidence')

    for e in recovered:
        # Nothing says these were made for Field's — see the note in the data —
        # so none of them may claim it.
        check(e['exclusive_to'] is None,
              f'recovered {e["name"]} claims to be exclusive to a retailer')
        check(not e['exclusivity_evidence'] and not e['in_custom_category'],
              f'recovered {e["name"]} carries shop-era evidence')
        check(e['image_provenance'] in ('archived_scan', 'archived_thumbnail',
                                       'live_site'),
              f'recovered {e["name"]} bad image_provenance '
              f'{e["image_provenance"]!r}')
        if e['image_provenance'] == 'live_site':
            # not in any archive: the file is still on Field's own server, so
            # the source is that URL rather than a capture of it.
            check(re.match(r'https://shop\.fieldsfabrics\.com/assets/images/'
                           r'ultrasuede/[0-9A-Za-z]+\.jpg$',
                           e['image_source'] or ''),
                  f'recovered {e["name"]} image_source is not a Field\'s '
                  'swatch photograph')
        else:
            check(re.match(r'https://web\.archive\.org/web/\d{14}/http',
                           e['image_source'] or ''),
                  f'recovered {e["name"]} image_source is not an archive URL')
            check('/swatches/' in (e['image_source'] or ''),
                  f'recovered {e["name"]} image did not come out of Field\'s '
                  'swatch folder')

    # the membership rule, re-derived from the snapshot filenames: every Field's
    # LT product code held here is either one of Toray's 36 or a custom colour.
    prod_codes = {os.path.basename(p)[:4] for p in
                  glob.glob(os.path.join(fdir, 'products', '*.html'))
                  if os.path.getsize(p) > 0}
    cust_codes = {e['code'] for e in custom}
    check(prod_codes, 'no Field\'s product snapshots found')
    for c in sorted(prod_codes):
        check(c in off_codes or c in cust_codes,
              f'Field\'s product {c} is neither official nor custom')
    for c in sorted(cust_codes):
        check(c not in off_codes, f'custom {c} is also official')
    basis = data['meta']['fields_custom']['basis_counts']
    check(sum(basis.values()) == len(custom),
          'basis_counts does not add up to the custom colour count')
    check(basis['absent_from_official_line'] ==
          sum(1 for e in custom if e['custom_basis'] == 'absent_from_official_line'),
          'basis_counts absent_from_official_line is wrong')

    # --- nap blocks ---------------------------------------------------------
    # The site draws these instead of the photographs, so a wrong axis or a
    # contrast of zero is a swatch rendered flat and plastic, not a crash.
    def check_nap(e, kind, measurable):
        n = e.get('nap')
        if not e.get('rgb'):
            check(n is None, f'{kind} {e["name"]} has no rgb but carries a nap')
            return
        if not check(isinstance(n, dict), f'{kind} {e["name"]} has no nap'):
            return
        check(set(n) == {'axis', 'contrast', 'contrast_source'},
              f'{kind} {e["name"]} nap keys are {sorted(n)}')
        check(len(n['axis']) == 3, f'{kind} {e["name"]} axis is not a triple')
        check(all(0.2 <= v <= 2.5 for v in n['axis']),
              f'{kind} {e["name"]} axis out of range: {n["axis"]}')
        # the axis is normalised to unit luminance, so it always weighs 1
        luma = sum(v * w for v, w in zip(n['axis'], (0.2126, 0.7152, 0.0722)))
        check(abs(luma - 1) < 0.005,
              f'{kind} {e["name"]} axis luminance is {luma:.4f}, expected 1')
        # structural contrast only — the pixel-noise band is measured out, and
        # a figure back up in the old 8-to-12 range means it has crept back in
        check(0.5 <= n['contrast'] <= 6.0,
              f'{kind} {e["name"]} contrast {n["contrast"]} is not plausible')
        check(n['contrast_source'] in ('measured', 'modeled'),
              f'{kind} {e["name"]} bad contrast_source {n["contrast_source"]!r}')
        # measured means, and only means, that a big enough clean frame existed
        check(n['contrast_source'] == ('measured' if measurable(e) else 'modeled'),
              f'{kind} {e["name"]} is {n["contrast_source"]} but its image says '
              'otherwise')

    for c in colors:
        check_nap(c, 'colour', lambda e: bool(e['image_large']))
    for e in custom:
        # Field's photographs are modelled whether or not they are large enough
        check_nap(e, 'custom', lambda e: False)
    for p in patterns:
        check(p.get('nap') is None, f'pattern {p["name"]} carries a nap block')

    # a nap has to be able to stand in for the photo, so every renderable entry
    # needs both a hex and a nap, and the two counts have to agree.
    renderable = [e for e in colors + custom if e.get('hex')]
    check(len(renderable) == 106,
          f'{len(renderable)} renderable entries, expected 106')
    check(all(e.get('nap') for e in renderable), 'a renderable entry has no nap')
    check('nap_note' in data['meta'], 'meta has no nap_note')

    # --- pattern colourways and images ---------------------------------------
    # Six of the eleven patterns were sold in two colourways, which is what
    # makes seventeen entries. Two entries sharing a name is the data being
    # right; two sharing a (pattern, colour) would be it being wrong.
    keys = [(p['pattern'], p['color']) for p in patterns]
    check(len(set(keys)) == len(keys), 'two patterns share a pattern/colour pair')
    check(len({p['pattern'] for p in patterns}) == 11,
          f'{len({p["pattern"] for p in patterns})} pattern numbers, expected 11')
    doubled = {n for n in {p['name'] for p in patterns}
               if sum(1 for p in patterns if p['name'] == n) == 2}
    check(doubled == {'Baby Cougar', 'Bobcat', 'Cheetah', 'Jaguar', 'Python',
                      'Small Pony'},
          f'the two-colourway patterns are {sorted(doubled)}')
    for p in patterns:
        prov = p.get('image_provenance')
        if not p['image']:
            check(prov is None, f'pattern {p["name"]} has no image but a provenance')
            continue
        check(os.path.exists(os.path.join(ROOT, p['image'])),
              f'pattern {p["name"]} image {p["image"]} is missing')
        # Only the two Toray never captured may be anything but `wayback`, and
        # of those only Bobcat 231 has a real photograph: Field's own scan of
        # it, which has to be the file the live-site record names and has to
        # stay out of the ink reading — its logo clusters as an ink of its own
        # and its cast is a different generation of photography.
        stem = p['image'].rsplit('/', 1)[1][:-4]
        if stem == 'bobca231':
            check(prov == 'fields_live',
                  f'pattern {p["name"]} image_provenance is {prov!r}')
            shot = json.load(open(os.path.join(
                ROOT, 'research/live_swatch_images.json'))).get('177-231')
            check(shot and shot['image'] == p['image'],
                  'Bobcat 231 is not the file the live-site record names')
            check(p['slug'] not in p['colorway']['sampled_from'],
                  'Bobcat 231 is read for ink from its own Field\'s scan')
        else:
            check(prov == ('reference_photo' if stem == 'ocelo154' else 'wayback'),
                  f'pattern {p["name"]} image_provenance is {prov!r}')
    check('image_note' in data['meta']['light_jungle'],
          'light_jungle meta has no image_note')
    check('colorway_note' in data['meta']['light_jungle'],
          'light_jungle meta has no colorway_note')

    # --- what the colour numbers are ----------------------------------------
    #
    # The claim being checked is that the colour number is the ink combination
    # and not the print: every pattern carrying a number must carry the same
    # palette, and a name said to be Field's must be findable, printed beside
    # that number, in the catalogue text saved under research/ — read here out
    # of those files rather than out of the builder.
    catalogs = ''
    for fn in sorted(glob.glob(os.path.join(ROOT, 'research/fields_catalogs/*.txt'))
                     + glob.glob(os.path.join(
                         ROOT, 'research/fields_sample_sets/*.txt'))):
        catalogs += ' ' + ' '.join(
            open(fn, encoding='utf-8', errors='replace').read().split())

    ways = {}
    for p in patterns:
        way = p.get('colorway')
        check(bool(way), f'pattern {p["name"]} {p["color"]} has no colorway')
        if not way:
            continue
        check(way['code'] == p['color'],
              f'{p["name"]} carries colourway {way["code"]} under {p["color"]}')
        # the same number, the same inks, wherever it appears
        first = ways.setdefault(way['code'], way)
        check(json.dumps(first, sort_keys=True) == json.dumps(way, sort_keys=True),
              f'colourway {way["code"]} differs between patterns')
        check(way['name'] == '/'.join(c['name'] for c in way['colors']),
              f'colourway {way["code"]} name does not match its colours')
        for ink in way['colors']:
            check(re.fullmatch(r'#[0-9a-f]{6}', ink['hex']),
                  f'colourway {way["code"]} has a bad hex {ink["hex"]!r}')
            check(ink['hex'] == '#%02x%02x%02x' % tuple(ink['rgb']),
                  f'colourway {way["code"]} hex and rgb disagree')
        check(1 < len(way['colors']) < 4,
              f'colourway {way["code"]} has {len(way["colors"])} inks')
        # a palette is only ever read off photographs that exist
        for slug in way['sampled_from']:
            src_p = next((q for q in patterns if q['slug'] == slug), None)
            check(src_p is not None and src_p['image'],
                  f'colourway {way["code"]} sampled from {slug}, which has no image')
            check(src_p is None or src_p['color'] == way['code'],
                  f'colourway {way["code"]} sampled from {slug}, a different one')
        provs = {next(q['image_provenance'] for q in patterns if q['slug'] == s)
                 for s in way['sampled_from']}
        check(way['hex_source'] == ('reference_photo' if 'reference_photo' in provs
                                    else 'archived_photo'),
              f'colourway {way["code"]} hex_source is {way["hex_source"]!r}')

        if way['name_source'] == 'fields_catalog':
            for code in way['named_on']:
                pat, col = code.split('-')
                check(col == way['code'],
                      f'colourway {way["code"]} claims to be named on {code}')
                # the number and the name on one line of a saved catalogue,
                # allowing the one abbreviation Field's used for a colour name
                names = r'\s*/\s*'.join(
                    r'(?:Black|Blk\.?)' if c['name'] == 'Black'
                    else re.escape(c['name']) for c in way['colors'])
                check(re.search(rf'#?{int(pat)}-{col}(?:-\d\d)?\b[^#\d]{{0,40}}?'
                                rf'{names}', catalogs, re.I),
                      f'{code} is not printed as {way["name"]} in any catalogue')
        else:
            check(way['name_source'] == 'estimated',
                  f'colourway {way["code"]} name_source is '
                  f'{way["name_source"]!r}')
            check('named_in' not in way and 'named_on' not in way,
                  f'colourway {way["code"]} is estimated but cites a naming')

    check(len(ways) == 10, f'{len(ways)} colourways, expected 10')
    check({c for c, w in ways.items() if w['name_source'] == 'fields_catalog'}
          == {'023', '231', '232'},
          'the colourways Field\'s named are not 023, 231 and 232')
    check('color_number_note' in data['meta']['light_jungle'],
          'light_jungle meta has no color_number_note')
    check('colorway_hex_note' in data['meta']['light_jungle'],
          'light_jungle meta has no colorway_hex_note')

    # --- colour cards -------------------------------------------------------
    for s in data['sources']:
        if s.get('local_file'):
            fp = os.path.join(ROOT, s['local_file'])
            check(os.path.exists(fp), f'missing colour card {s["local_file"]}')
            if os.path.exists(fp):
                d = open(fp, 'rb').read()
                check(d[:4] == b'%PDF', f'{s["local_file"]} is not a PDF')
                check(d.rstrip()[-5:] == b'%%EOF', f'{s["local_file"]} looks truncated')

    # --- the pre-2011 Light record ------------------------------------------
    #
    # Re-read straight out of research/, not out of the builder's own
    # intermediate: every colour claimed here has to be findable, by number and
    # by name, in the tag-stripped text of a capture actually held on disk.
    # Both halves of that record are checked together: a colour whose scan was
    # recovered moved in with the custom colours, but it is still a name off a
    # Field's list page and still has to be found on one.
    historical = data['historical_colors']
    old_lists = historical + recovered
    check(len(old_lists) == 69, f'{len(old_lists)} pre-2011 colours, expected 69')
    check(len(historical) == 13,
          f'{len(historical)} with nothing to show, expected 13')

    old_text = open(os.path.join(ROOT, 'research/fields_oldsite/old_alltext.txt'),
                    encoding='utf-8', errors='replace').read()
    catalog_text = ''
    for fn in sorted(glob.glob(os.path.join(ROOT, 'research/fields_catalogs/*.txt'))):
        catalog_text += open(fn, encoding='utf-8', errors='replace').read()
    # the 2008-08 catalogue is a JBIG2 scan with no text layer; it was read from
    # a render and contributes nothing to a grep, which is why the check below
    # accepts a colour that only the list pages carry.
    corpus = old_text + catalog_text

    off_and_former = {c['code'] for c in colors}
    for c in colors:
        off_and_former |= {f['code'] for f in c.get('former_skus', [])}

    hist_codes = set()
    for e in old_lists:
        check(e['code'] not in hist_codes, f'duplicate historical code {e["code"]}')
        hist_codes.add(e['code'])
        # the whole membership test: Toray never carried this number, under any
        # SKU it ever had. #5832 is White's own pre-2010 code and stays out.
        check(e['code'] not in off_and_former,
              f'historical {e["name"]} #{e["code"]} is an official code')
        check(e['sku'] is None, f'historical {e["name"]} has a Toray SKU')
        check(e['first_seen'] <= e['last_seen'], f'historical {e["name"]} dates reversed')
        check(e['name'] in e['name_variants'] or
              any(v.startswith(e['name']) for v in e['name_variants']),
              f'historical {e["name"]} is not one of its own variants')
        # the number, printed, somewhere in the saved evidence
        check(f'#{e["code"]}' in corpus or f'# {e["code"]}' in corpus,
              f'historical #{e["code"]} not in any saved capture')
        # and the name beside it, on at least one of those lines
        check(re.search(rf'#\s*{e["code"]}\s+{re.escape(e["name"].split(" -")[0])}',
                        corpus, re.I),
              f'historical #{e["code"]} is not printed as "{e["name"]}"')
        check(e['captures'], f'historical {e["name"]} has no captures')
        for cap in e['captures']:
            check(cap['archive_url'].startswith('https://web.archive.org/web/'),
                  f'historical {e["name"]} capture is not an archive URL')
        check(e['source'] == e['captures'][-1]['archive_url'],
              f'historical {e["name"]} source is not its last capture')

    # what is left in historical_colors is exactly what has no picture
    for e in historical:
        check(e['hex'] is None and e['image'] is None and e['nap'] is None,
              f'historical {e["name"]} carries colour it cannot have')
        check(e['code'] not in {x['code'] for x in shop},
              f'historical {e["name"]} #{e["code"]} is also a shop-era code')

    # and the recovered ones trace back to a scan that is still on disk
    scans = json.load(open(os.path.join(ROOT, 'research/old_swatch_images.json')))
    shots = json.load(open(os.path.join(ROOT, 'research/live_swatch_images.json')))
    check(not (set(scans) & set(shots)),
          'a colour is claimed by both the scan record and the live-site record')

    for e in recovered:
        if e['image_provenance'] != 'live_site':
            continue
        # the nine with no capture anywhere: the file has to be the one the
        # live-site record names, still on disk, and still the colour on the
        # page when it is resampled from scratch.
        shot = shots.get(e['code'])
        if not check(shot,
                     f'recovered {e["name"]} has no entry in the live-site record'):
            continue
        check(e['image_source'] == shot['source'],
              f'recovered {e["name"]} image_source is not the file on record')
        check(e['image'] == shot['image'],
              f'recovered {e["name"]} image is not the file on record')
        img = os.path.join(ROOT, e['image'] or '')
        if not check(e['image'] and os.path.exists(img),
                     f'recovered {e["name"]} photograph is missing'):
            continue
        check(open(img, 'rb').read(2) == b'\xff\xd8',
              f'recovered {e["name"]} photograph is not a JPEG')
        check(paper_free(img),
              f'recovered {e["name"]} still has scanner paper in the frame')
        got = corner_median(img, 0.06, 0.16)
        check(got == e['rgb'],
              f'recovered {e["name"]} samples {got}, data says {e["rgb"]}')
        # a stand-in from another weight has to say so, and to say which
        based = e.get('based_on')
        check(bool(based) == bool(shot.get('weight')),
              f'recovered {e["name"]} disagrees with the record about whether '
              'its photograph is of another weight')
        if based:
            check(based['code'] == shot['code'] and based['weight'] == shot['weight'],
                  f'recovered {e["name"]} based_on does not match the record')
            check(e['image'].endswith(f'/{based["code"]}.jpg'),
                  f'recovered {e["name"]} shows a file that is not #{based["code"]}')
            # the pairing is a catalogue sheet, not a shared name: both numbers
            # have to be printed against the name in the catalogue text.
            for code in (e['code'], based['code']):
                check(re.search(rf'#\s*{code}\b', catalog_text),
                      f'#{code} is not in any Field\'s catalogue held here')

    for e in recovered:
        if e['image_provenance'] == 'live_site':
            continue
        rec = scans.get(e['code'])
        if not check(rec, f'recovered {e["name"]} has no entry in the scan record'):
            continue
        check(e['image_source'] == rec['archive_url'],
              f'recovered {e["name"]} image_source is not the capture on record')
        raw = os.path.join(ROOT, f'research/swatches_archive/{e["code"]}.jpg')
        if check(os.path.exists(raw), f'recovered {e["name"]} raw scan is missing'):
            check(open(raw, 'rb').read(2) == b'\xff\xd8',
                  f'recovered {e["name"]} raw scan is not a JPEG')
        full = rec['size'] == 'full'
        # A thumbnail exists twice over: the research copy, which is what the
        # colour was read off, and a squared copy of it published as the
        # photograph. The colour is checked against the research copy — the
        # same file the builder reads — so that squaring a frame to fit the
        # panel can never move a colour, and the published one is checked for
        # being there and being square.
        cropped = os.path.join(ROOT, e['image'] if full else
                               f'research/swatches_cropped/{e["code"]}.jpg')
        if not check(os.path.exists(cropped),
                     f'recovered {e["name"]} cropped scan is missing'):
            continue
        if not full:
            shown = os.path.join(ROOT, e['image'] or '')
            if check(e['image'] and os.path.exists(shown),
                     f'recovered {e["name"]} published thumbnail is missing'):
                w, h = Image.open(shown).size
                check(w == h,
                      f'recovered {e["name"]} published thumbnail is {w}x{h}, '
                      'not square')
        # the whole point of the crop: no scanner paper left in the frame, or
        # the median is reading the desk rather than the cloth
        check(paper_free(cropped),
              f'recovered {e["name"]} still has scanner paper in the frame')
        # and the hex on the site is that file, resampled from scratch
        got = corner_median(cropped, 0.06, 0.16) if full \
            else corner_median(cropped, 0.04, 0.30)
        check(got == e['rgb'],
              f'recovered {e["name"]} samples {got}, data says {e["rgb"]}')

    # the two names this set exists for, and one that came back with a picture
    for code, name in (('4599', 'Active Green'), ('8281', 'Orange Sherbet'),
                       ('8221', 'Marmalade')):
        e = next((x for x in old_lists if x['code'] == code), None)
        if check(e, f'historical #{code} {name} is missing'):
            check(e['name'] == name, f'#{code} is "{e["name"]}", expected {name}')

    # every list-page capture a historical entry points at is a file on disk
    saved_ts = {re.search(r'_(\d{14})\.html$', fn).group(1)
                for fn in glob.glob(os.path.join(
                    ROOT, 'research/fields_oldsite/*_[0-9]*.html'))}
    for e in old_lists:
        for cap in e['captures']:
            m = re.search(r'/web/(\d{14})/', cap['archive_url'])
            if cap['in'] != "Field's Ultrasuede catalogue":
                check(m.group(1) in saved_ts,
                      f'historical {e["name"]} cites uncaptured {m.group(1)}')

    # both halves of the one cross-reference in the data point at each other
    for e in historical + custom:
        if e.get('see_also'):
            other = {'custom_colors': custom,
                     'historical_colors': historical}[e['see_also']['set']]
            back = next((x for x in other if x['code'] == e['see_also']['code']), None)
            if check(back, f'{e["name"]} see_also #{e["see_also"]["code"]} not found'):
                check(back.get('see_also', {}).get('code') == e['code'],
                      f'{e["name"]} see_also is not reciprocated')
                # a see_also exists because two entries carry one name, but
                # not always one spelling of it: "LT Blue" and "Lt. Blue".
                flat = lambda n: re.sub(r'[^a-z0-9]', '', n.lower())
                check(flat(back['name']) == flat(e['name']),
                      f'{e["name"]} see_also points at a different name')

    # --- optional link check ------------------------------------------------
    if '--links' in sys.argv:
        urls = ({c['source'] for c in colors} | {p['source'] for p in patterns} |
                {e['source'] for e in custom} |
                {e['product_page_source'] for e in custom} |
                {e['archived_swatch']['archive_url'] for e in custom
                 if e.get('archived_swatch')} |
                {cap['archive_url'] for e in old_lists for cap in e['captures']})
        for s in data['sources']:
            urls |= {s[k] for k in ('archive_url', 'latest_archive_url') if s.get(k)}
            for cap in s.get('captures', []):
                urls.add(cap['archive_url'])
        print(f'checking {len(urls)} distinct archive URLs...')
        for u in sorted(urls):
            # web.archive.org rate-limits hard: a bare loop starts returning
            # connection failures (curl "000") after ~20 requests, so back off
            # and retry rather than reporting those as dead links.
            for attempt in range(1, 6):
                code = subprocess.run(
                    ['curl', '-sIL', '-o', '/dev/null', '-w', '%{http_code}',
                     '--max-time', '60', u],
                    capture_output=True, text=True).stdout.strip()
                if code == '200':
                    break
                time.sleep(attempt * 5)
            check(code == '200', f'{code} for {u}')
            print(f'  {code}  {u[:110]}')
            time.sleep(1)

    print(f'\n{checks} checks, {len(fails)} failures')
    for f in fails:
        print('  FAIL:', f)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
