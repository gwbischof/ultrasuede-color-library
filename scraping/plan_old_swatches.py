#!/usr/bin/env python3
"""Pick an archived scan for every pre-2011 Field's colour, and emit a fetch list.

Field's old list pages hung a swatch scan off every colour number — "Click on
color number to see a swatch" — at /swatches/<number>.jpg, and a matching
postage stamp at /swatches/thumb/<number>.jpg for the view-by-swatch pages.
Those scans are the only surviving picture of any of these colours.

Two things are decided here rather than in the builder, because both are about
which bytes to fetch:

  * Which capture. A filename Field's reused would give the wrong colour, so
    the capture taken is the one closest in time to the page capture that linked
    it — the picture that page was showing.
  * Which size. The full scans are ~400px and crop and sample cleanly. The
    thumbnails are ~100px: enough to take a median colour off, and a poor
    picture rather than no picture, so they are fetched and marked `thumb` —
    read with wider sample boxes, and published squared, at a size the panel
    has to stretch.
"""
import json, os, re, glob, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESEARCH = os.path.join(ROOT, 'research')
OLDSITE = os.path.join(RESEARCH, 'fields_oldsite')
SWATCH_CDX = os.path.join(RESEARCH, 'cdx', 'cdx_swatches.json')
OUT_JSON = os.path.join(RESEARCH, 'old_swatch_images.json')
OUT_TSV = os.path.join(ROOT, 'scraping', 'old_swatch_jobs.tsv')
RAW = os.path.join(RESEARCH, 'swatches_archive')

PAGE_RE = re.compile(r'(lgtlist|wide_list|spec_list)_(\d{14})\.html$')
LINK_RE = re.compile(
    r'<a\s[^>]*href="([^"]*swatches/[^"]+?\.jpe?g)"[^>]*>(.*?)</a>', re.I | re.S)
CODE_RE = re.compile(r'#\s*(\d{2,5}S?)')

# /swatches/<n>.jpg and /swatches/disc/<n>.jpg are the full scans; the thumb
# directories hold the same scans at postage-stamp size. Anything under
# uleather/ or thumb/leather/ is a different product line and is not a fallback
# for a Light colour that happens to share a number.
FULL_RE = re.compile(r'/swatches/(?:disc/)?([^/]+)\.jpe?g$', re.I)
THUMB_RE = re.compile(r'/swatches/(?:disc/)?thumb(?:nails)?/([^/]+)\.jpe?g$', re.I)


def links():
    """code -> {swatch filename -> [page capture timestamps that linked it]}."""
    out = collections.defaultdict(lambda: collections.defaultdict(list))
    for path in sorted(glob.glob(os.path.join(OLDSITE, '*.html'))):
        m = PAGE_RE.search(os.path.basename(path))
        if not m:
            continue
        html = open(path, 'rb').read().decode('windows-1252')
        for href, label in LINK_RE.findall(html):
            code = CODE_RE.search(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', label)))
            if code:
                name = re.search(r'([^/]+)\.jpe?g$', href, re.I).group(1)
                out[code.group(1)][name].append(m.group(2))
    return out


def captures():
    """(size, filename) -> [(timestamp, original url)] over every archived scan."""
    out = collections.defaultdict(list)
    for orig, ts, _status in json.load(open(SWATCH_CDX))[1:]:
        m = THUMB_RE.search(orig)
        size = 'thumb'
        if not m:
            m, size = FULL_RE.search(orig), 'full'
        if m:
            out[(size, m.group(1))].append((ts, orig))
    return out


def pick(files, archived, size):
    """Closest capture at `size` to a page capture that linked one of `files`."""
    best = None
    for name, pages in sorted(files.items()):
        for ts, orig in archived.get((size, name), []):
            gap = min(abs(int(ts) - int(p)) for p in pages) if pages else 0
            if best is None or gap < best[0]:
                best = (gap, ts, orig, name, sorted(pages))
    return best


def main():
    lt = json.load(open(os.path.join(ROOT, 'lt.json')))
    historical = {c['code']: c['name'] for c in lt['historical_colors']}
    linked, archived = links(), captures()

    chosen, missing = {}, []
    for code in sorted(historical):
        files = dict(linked.get(code, {}))
        # A colour whose number never appeared as a link — the swatch pages that
        # carried it were not archived — can still have its scan sitting in the
        # same folder under the same number.
        match = 'linked' if files else 'filename'
        if not files:
            files = {code: []}
        for size in ('full', 'thumb'):
            best = pick(files, archived, size)
            if best:
                break
        if not best:
            missing.append(code)
            continue
        _gap, ts, orig, name, pages = best
        chosen[code] = {
            'file': name,
            'size': size,
            'match': match,
            'timestamp': ts,
            'original_url': orig,
            'archive_url': f'https://web.archive.org/web/{ts}/{orig}',
            'linked_from': pages,
        }

    json.dump(chosen, open(OUT_JSON, 'w'), indent=1, sort_keys=True)
    os.makedirs(RAW, exist_ok=True)
    with open(OUT_TSV, 'w') as fh:
        for code, rec in sorted(chosen.items()):
            dest = os.path.relpath(os.path.join(RAW, f'{code}.jpg'),
                                   os.path.join(ROOT, 'scraping'))
            fh.write(f"{dest}\t{rec['timestamp']}\t{rec['original_url']}\n")

    sizes = collections.Counter(r['size'] for r in chosen.values())
    print(f'{len(historical)} historical colours | {len(chosen)} with an archived '
          f'scan ({sizes["full"]} full, {sizes["thumb"]} thumbnail only)')
    print('by filename alone:',
          ', '.join(f'#{c}' for c, r in sorted(chosen.items())
                    if r['match'] == 'filename') or 'none')
    print('no scan:', ', '.join(f'#{c} {historical[c]}' for c in missing))


if __name__ == '__main__':
    main()
