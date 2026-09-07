#!/usr/bin/env python3
"""Crop the archived Field's swatch scans down to the cloth.

Every one of these is a square of Ultrasuede laid on a scanner: white paper
around it, a cut edge and its shadow, and Field's logo dropped in white across
the middle. What the dataset wants is the cloth, so the paper is found and cut
away and the frame pulled well inside the cut edge. The logo is left where it
is — the builder samples these from the four corners, the same way it reads
Field's watermarked product photos, and never goes near the middle.

Full scans (~400px) are written into images/ and published as the colour's
photograph. Thumbnails (~100px) go to research/, and that copy is the one the
builder samples — left exactly as it falls out of here, so the colours never
move. A squared copy of each also goes to images/ and is published. Six colours
have no full scan anywhere in the archive, and a soft 57px square of the real
cloth says more than an empty frame; they are squared here rather than left for
the page to crop square, which would take a tenth off the widest of them.
"""
import json, os
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'research', 'swatches_archive')
RECORD = os.path.join(ROOT, 'research', 'old_swatch_images.json')
OUT = {'full': os.path.join(ROOT, 'images', 'fields_old'),
       'thumb': os.path.join(ROOT, 'research', 'swatches_cropped')}

PAPER = 24      # channel distance from the scanner background that reads as cloth
COVER = 0.5     # a row is inside the swatch once half of it is cloth
CLOSE = 0.10    # ... and a shorter gap than this is something lying on it
INSET = 0.12    # and then this much of the swatch is given up on every side
FLOOR = 0.35    # a "swatch" smaller than this much of the frame is not believed


def span(inside):
    """The swatch's extent along one axis, from a profile of cloth coverage.

    Two different scanning accidents have to survive this. #2608 has a dark
    four-pixel strip down its right edge, ninety columns clear of the cloth, so
    first-to-last reaches out and drags the crop across the paper between them.
    #2894's white logo band takes two dozen rows through the middle below any
    coverage threshold, so longest-run stops at the band. Gaps up to CLOSE are
    closed first — a band inside the swatch — and the longest of what is left is
    the swatch — never the strip, which no plausible gap reaches.
    """
    runs, start = [], None
    for i, v in enumerate(list(inside) + [False]):
        if v and start is None:
            start = i
        elif not v and start is not None:
            runs.append([start, i])
            start = None
    if not runs:
        return None
    close = CLOSE * len(inside)
    merged = [runs[0]]
    for lo, hi in runs[1:]:
        if lo - merged[-1][1] <= close:
            merged[-1][1] = hi
        else:
            merged.append([lo, hi])
    return tuple(max(merged, key=lambda r: r[1] - r[0]))


def bbox(a):
    """Box of the cloth in a scan, or None if the paper cannot be told from it."""
    border = np.concatenate([a[:4].reshape(-1, 3), a[-4:].reshape(-1, 3),
                             a[:, :4].reshape(-1, 3), a[:, -4:].reshape(-1, 3)])
    paper = np.median(border, axis=0)
    cloth = np.abs(a - paper).max(axis=2) > PAPER
    ends = [span(cloth.mean(axis=ax) > COVER) for ax in (1, 0)]
    if None in ends:
        return None
    (y0, y1), (x0, x1) = ends
    if (y1 - y0) < FLOOR * a.shape[0] or (x1 - x0) < FLOOR * a.shape[1]:
        return None
    return x0, y0, x1, y1


def crop(path):
    im = Image.open(path).convert('RGB')
    a = np.asarray(im).astype(np.int16)
    box = bbox(a) or (0, 0, im.size[0], im.size[1])
    x0, y0, x1, y1 = box
    dx, dy = int((x1 - x0) * INSET), int((y1 - y0) * INSET)
    return im.crop((x0 + dx, y0 + dy, x1 - dx, y1 - dy)), box


def square(im):
    """Centre the shorter side, for a thumbnail on its way to being published.

    The panel holds a shader and its photograph in one square box, so anything
    off square is cropped to fit by the browser. These are the only photographs
    in the set that are not square already — a thumbnail is small enough that
    the paper edge lands between pixels — and losing the cloth evenly off both
    sides here beats losing it all off one side there.
    """
    w, h = im.size
    side = min(w, h)
    x, y = (w - side) // 2, (h - side) // 2
    return im.crop((x, y, x + side, y + side))


def main():
    record = json.load(open(RECORD))
    for d in OUT.values():
        os.makedirs(d, exist_ok=True)
    kept, guessed = 0, []
    for code, rec in sorted(record.items()):
        src = os.path.join(RAW, f'{code}.jpg')
        if not os.path.exists(src):
            continue
        im, box = crop(src)
        raw = Image.open(src).size
        if box == (0, 0, raw[0], raw[1]):
            guessed.append(code)
        im.save(os.path.join(OUT[rec['size']], f'{code}.jpg'), quality=92)
        # a thumbnail is both the sampling copy above and, squared, the
        # published photograph — the only one these six colours have
        if rec['size'] == 'thumb':
            square(im).save(os.path.join(OUT['full'], f'{code}.jpg'), quality=92)
        kept += 1
        print(f'{code:>5}  {raw[0]}x{raw[1]} -> {im.size[0]}x{im.size[1]}  {rec["size"]}')
    print(f'\n{kept} cropped')
    print('paper not found (whole frame used):', ', '.join(guessed) or 'none')


if __name__ == '__main__':
    main()
