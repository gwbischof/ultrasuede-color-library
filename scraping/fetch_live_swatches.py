#!/usr/bin/env python3
"""Pull the Field's swatch photographs that no archive kept.

Field's leaves swatch photography in assets/images/ultrasuede/ long after the
product itself is gone, so a colour with nothing in the Wayback Machine can
still have a picture on their live site. Two kinds turn up there:

  - the colour under its own Light number, which is simply its photograph; and
  - the colour under the number the *same colour* carries in another weight,
    which is a stand-in and is labelled as one on the page.

The collection's one unphotographed print, Bobcat 177-231, comes out of the same
folder under its own pattern number, and is written into images/jungle/ where the
builder looks for it.

The second kind is only taken where a Field's catalogue prints the two numbers
in adjacent sections of one sheet — #4599 Active Green under Light and #4598
Active Green under Soft, on the January 2007 sheet — which is what makes the
pairing a record rather than a guess. A shared name on its own is not enough.

Two generations of photograph live in that folder. The newer ones are 600px and
carry the "Field's FABRICS ONLINE STORE" watermark; the older are ~100px flatbed
scans with the script "Field's" logo, the same scans the old list pages linked.
Either way the builder reads them from the four corners and never goes near the
middle, so the logo is left alone — but a scan that still has scanner paper
around it is cropped down to the cloth first, by the same routine the archived
scans go through.

    python3 scraping/fetch_live_swatches.py
"""
import json, os, subprocess, sys, time
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from crop_old_swatches import crop  # noqa: E402  (same paper-finding routine)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'research', 'swatches_live')
OUT = os.path.join(ROOT, 'images', 'fields')
RECORD = os.path.join(ROOT, 'research', 'live_swatch_images.json')
BASE = 'https://shop.fieldsfabrics.com/assets/images/ultrasuede'

# Light colour number -> the Field's number its photograph is filed under, and
# the weight that number belongs to when it is not Light. Keyed by the Light
# number so the builder can ask "is there a picture of this colour anywhere".
WANTED = {
    # under their own number: these are photographs of the Light colour itself
    '2805':  {'code': '2805'},
    # the one Light Jungle colourway Toray never photographed. Field's filed a
    # scan of it under the pattern's own number, and their scan of 177-023 is
    # what identifies it: both show the same drawing — large solid rounded
    # spots, not the open rosettes of Jaguar 176 or Baby Cougar 181 — at the
    # same magnification, which is coarser than Toray's own close crops.
    '177-231': {'code': '177-231', 'kind': 'pattern',
                'out': 'images/jungle/bobca231.jpg'},
    '3968':  {'code': '3968'},
    '6647':  {'code': '6647'},
    '7369S': {'code': '7369S'},
    '8281':  {'code': '8281'},
    '9378':  {'code': '9378'},
    '9464':  {'code': '9464'},
    # under another weight's number: same colour, different cloth
    '4599':  {'code': '4598', 'weight': 'ST',
              'evidence': "Field's January 2007 Ultrasuede sheet prints #4599 "
                          'Active Green under ULTRASUEDE® LIGHT Solids and '
                          '#4598 Active Green under Soft'},
    '8276':  {'code': '8275', 'weight': 'ST',
              'evidence': "Field's February 2010 Ultrasuede sheet prints #8276 "
                          'Burnt Orange under ULTRASUEDE® LIGHT and #8275 '
                          'Burnt Orange under Soft'},
}


def fetch(code):
    dst = os.path.join(RAW, f'{code}.jpg')
    if os.path.exists(dst):
        return dst
    url = f'{BASE}/{code}.jpg'
    # curl rather than urllib: the system Pythons here ship without a CA bundle,
    # and this is one fetch of one file, not a reason to vendor certifi.
    data = subprocess.run(['curl', '-sSLf', '--max-time', '60', url],
                          capture_output=True, check=True).stdout
    if not data.startswith(b'\xff\xd8'):
        raise SystemExit(f'{url} did not answer with a JPEG')
    open(dst, 'wb').write(data)
    time.sleep(1)
    return dst


def main():
    for d in (RAW, OUT):
        os.makedirs(d, exist_ok=True)
    record = {}
    for light, want in sorted(WANTED.items()):
        code = want['code']
        src = fetch(code)
        raw = Image.open(src).size
        im, box = crop(src)
        cropped = box != (0, 0, raw[0], raw[1])
        # crop() gives up and hands back the whole frame when it cannot tell
        # paper from cloth, which for these is the right answer: Field's has
        # already trimmed the newer photographs to the cloth.
        out = want.get('out', f'images/fields/{code}.jpg')
        dst = os.path.join(ROOT, out)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        (im if cropped else Image.open(src).convert('RGB')).save(dst, quality=92)
        record[light] = dict(want, source=f'{BASE}/{code}.jpg', image=out,
                             retrieved=time.strftime('%Y-%m-%d'),
                             cropped=cropped)
        print(f'{light:>6} <- {code:<6} {raw[0]}x{raw[1]}'
              f'{" cropped to %dx%d" % im.size if cropped else ""}'
              f'{"  [%s]" % want["weight"] if want.get("weight") else ""}')
    with open(RECORD, 'w', encoding='utf-8') as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print(f'\n{len(record)} colours, {sum(1 for r in record.values() if r.get("weight"))} '
          'of them standing in from another weight')


if __name__ == '__main__':
    main()
