#!/usr/bin/env python3
"""Probe Field's asset folders for the code+name filename shape.

LT Blue's photograph is filed as assets/images/100lightblue.jpg -- part number
followed by the colour name, lowercased and stripped of spaces. Nothing else on
the site is named that way consistently, so it is worth walking that shape over
the codes that still have no picture before calling the live server exhausted.
"""
import json, os, re, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'research', 'probe_named.json')

BASES = ['https://shop.fieldsfabrics.com/assets/images',
         'https://shop.fieldsfabrics.com/assets/images/ultrasuede']

WANT = {
    '8215': 'Bird of Paradise', '2714': 'Blue', '9467': 'Bright Violet',
    '9372': 'Eggplant', '4619': 'Green Glass', '7369': 'Navajo Turquoise',
    '6635': 'Rapture Rose', '2465': 'Royal', '2708': 'Sky Blue',
    '684': 'Soft Ivy', '452': 'Spanish Gold', '7361': 'Teal Blue',
    '5837': 'White Extra Supple', '7000': 'Aqua', '8200': 'Cinnamon',
    '3835': 'Henna', '3800': 'Rustola', '9270': 'Ultraviolet',
    '9364': 'Wisteria',
}


def shapes(code, name):
    flat = re.sub(r'[^a-z0-9]', '', name.lower())
    dash = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    for stem in {f'{code}{flat}', f'{code}-{dash}', f'{code}lt{flat}',
                 f'{code}light{flat}', f'{code}{flat}lt', flat,
                 f'ultrasuede{flat}', f'lt{code}{flat}'}:
        yield f'{stem}.jpg'
        yield f'{stem}_thumbnail.jpg'


def main():
    hits, tried = {}, 0
    for code, name in WANT.items():
        for base in BASES:
            for fn in shapes(code, name):
                url = f'{base}/{fn}'
                r = subprocess.run(['curl', '-sSL', '--max-time', '25',
                                    '-w', '\n%{http_code}', url],
                                   capture_output=True)
                body, _, status = r.stdout.rpartition(b'\n')
                tried += 1
                if status.decode().strip() == '200' and body.startswith(
                        (b'\xff\xd8', b'GIF8', b'\x89PNG')):
                    hits.setdefault(code, []).append({'url': url,
                                                      'bytes': len(body)})
                    print(f'  HIT {code:>6} {len(body):>8}b {url}', flush=True)
                time.sleep(0.2)
        print(f'{code:>6} {name:<20} {len(hits.get(code, []))} hit(s)', flush=True)
    json.dump({'tried': tried, 'hits': hits}, open(OUT, 'w'), indent=2)
    print(f'\n{tried} URLs tried, {sum(len(v) for v in hits.values())} found')


if __name__ == '__main__':
    main()
