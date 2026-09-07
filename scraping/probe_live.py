#!/usr/bin/env python3
"""Probe Field's live server for swatch files under the codes still missing one.

Field's leaves swatch photography on disk long after the product is gone, so a
colour with nothing in the Wayback Machine can still have a file there. This
walks every filename shape seen in that folder against every code that has no
picture, and records what answered.
"""
import json, os, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'research', 'probe_live.json')

BASES = [
    'https://shop.fieldsfabrics.com/assets/images/ultrasuede',
    'https://shop.fieldsfabrics.com/assets/images',
]
SUFFIXES = ['{c}.jpg', '{c}.gif', '{c}.png', '{c}S.jpg', '{c}s.jpg',
            '{c}_thumbnail.jpg', '{c}-58.jpg', '{c}lt.jpg']

CODES = sys.argv[1:] or [
    # historical_colors, nothing at any size
    '8215', '2714', '9467', '9372', '4619', '7369', '6635', '2465', '2708',
    '684', '452', '7361', '5837',
    # custom_colors known only from a ~100px thumbnail
    '7000', '8200', '3835', '3800', '9270', '9364',
]


def head(url):
    r = subprocess.run(
        ['curl', '-sSI', '-o', '/dev/null', '--max-time', '30',
         '-w', '%{http_code} %{size_download} %{content_type}', url],
        capture_output=True, text=True)
    return r.stdout.strip()


def main():
    hits, tried = {}, 0
    for code in CODES:
        for base in BASES:
            for shape in SUFFIXES:
                url = f'{base}/{shape.format(c=code)}'
                r = subprocess.run(
                    ['curl', '-sSL', '--max-time', '30', '-w', '\n%{http_code}',
                     url], capture_output=True)
                body, _, status = r.stdout.rpartition(b'\n')
                status = status.decode().strip()
                tried += 1
                if status == '200' and body.startswith((b'\xff\xd8', b'GIF8', b'\x89PNG')):
                    hits.setdefault(code, []).append(
                        {'url': url, 'bytes': len(body)})
                    print(f'  HIT {code:>6}  {len(body):>7}b  {url}')
                time.sleep(0.3)
        print(f'{code:>6}  {len(hits.get(code, []))} hit(s)')
    json.dump({'tried': tried, 'hits': hits}, open(OUT, 'w'), indent=2)
    print(f'\n{tried} URLs tried, {sum(len(v) for v in hits.values())} files found '
          f'for {len(hits)} of {len(CODES)} codes')


if __name__ == '__main__':
    main()
