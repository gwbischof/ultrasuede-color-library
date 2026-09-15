#!/usr/bin/env python3
"""Render every nap swatch to an image, using the real shader.

    python3 export/render_swatches.py

Writes images/rendered/<sku>.webp — one per colour that carries a nap block.

Why this rather than a port: nap.js is the shader, and it is the only place the
octaves, the sheen, the sharpening and the seed are defined. Paneler needs a
static image per fabric and cannot run WebGL at build time. Reimplementing the
maths in Python would mean maintaining it twice and watching the two drift, so
this drives the actual shader in headless Chrome and commits what it draws.

No new dependency: system Chrome does WebGL headless given
--enable-unsafe-swiftshader. It needs an HTTP server because the harness fetches
the product JSON, which file:// forbids.

The harness lays out a grid; this screenshots it and slices it back apart. Cells
are paired to entries by index, so export/render_swatches.html must enumerate
products in the same order this does.
"""

import http.server
import json
import pathlib
import re
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'images' / 'rendered'
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

FILES = ['lx.json', 'st.json', 'lamous-th.json', 'shammy.json',
         'texvision-ds102.json', 'lt.json']
SECTIONS = ('colors', 'custom_colors')

# Filename key. NOT `sku`: all 70 of LT's custom colours have sku: null, so
# keying on it silently wrote every one of them to None.webp, each overwriting
# the last — 299 renders, 230 files, and a success message that counted writes
# rather than files. Product slug plus colour code is unique across the set, and
# assert_unique below fails the build rather than trusting that claim.
def key_for(fname, entry):
    return f"{fname.replace('.json', '')}-{entry['code']}"


SIZE = 512          # what Paneler's profile shelf wants at 3x; chips derive down
COLS = 6
BATCH = 48          # 6 x 8 cells => a 3072 x 4096 screenshot


def entries():
    """Every entry with something to draw, in the harness's own order."""
    out = []
    for f in FILES:
        doc = json.loads((ROOT / f).read_text())
        for sec in SECTIONS:
            for c in doc.get(sec) or []:
                if c.get('nap') and (c.get('rgb') or c.get('hex')):
                    out.append((f, c))
    return out


def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def translate_path(self, path):
            rel = path.split('?', 1)[0].lstrip('/')
            return str(ROOT / rel)

    httpd = socketserver.TCPServer(('127.0.0.1', 0), Quiet)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def shoot(port, start, count, dest):
    """Screenshot one grid batch. Returns the harness's status line."""
    rows = (count + COLS - 1) // COLS
    url = (f'http://127.0.0.1:{port}/export/render_swatches.html'
           f'?from={start}&count={count}&size={SIZE}&cols={COLS}')
    subprocess.run([
        CHROME, '--headless=new', '--enable-unsafe-swiftshader',
        '--hide-scrollbars', '--force-device-scale-factor=1',
        '--default-background-color=FFFFFFFF',
        f'--window-size={COLS * SIZE},{rows * SIZE}',
        f'--screenshot={dest}', '--virtual-time-budget=60000', url,
    ], check=True, capture_output=True, timeout=300)

    dom = subprocess.run([
        CHROME, '--headless=new', '--enable-unsafe-swiftshader',
        '--dump-dom', '--virtual-time-budget=60000', url,
    ], check=True, capture_output=True, timeout=300).stdout.decode('utf-8', 'replace')
    m = re.search(r'(READY[^<]*|ERROR[^<]*)', dom)
    return m.group(1) if m else 'no status'


def main():
    if not pathlib.Path(CHROME).exists():
        sys.exit(f'Chrome not found at {CHROME}')
    rows = entries()
    keys = [key_for(f, c) for f, c in rows]
    dupes = {k for k in keys if keys.count(k) > 1}
    if dupes:
        sys.exit(f'colliding swatch keys, would overwrite: {sorted(dupes)[:5]}')
    print(f'{len(rows)} swatches to render at {SIZE}px')

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    httpd, port = serve()
    written = 0
    try:
        with tempfile.TemporaryDirectory() as tmp:
            for start in range(0, len(rows), BATCH):
                batch = rows[start:start + BATCH]
                shot = pathlib.Path(tmp) / f'{start}.png'
                status = shoot(port, start, len(batch), shot)
                if not status.startswith('READY'):
                    sys.exit(f'batch {start}: {status}')
                drawn = int(re.search(r'drawn=(\d+)', status).group(1))
                if drawn != len(batch):
                    sys.exit(f'batch {start}: painted {drawn} of {len(batch)}')

                sheet = Image.open(shot).convert('RGB')
                for i, (_f, c) in enumerate(batch):
                    x, y = (i % COLS) * SIZE, (i // COLS) * SIZE
                    cell = sheet.crop((x, y, x + SIZE, y + SIZE))
                    # A cell that came out a flat colour means the shader did
                    # not run for it; the shader always leaves some variation.
                    if cell.convert('L').getextrema()[1] - \
                       cell.convert('L').getextrema()[0] < 2:
                        sys.exit(f'{c["sku"]}: rendered flat — shader did not draw')
                    cell.save(OUT / f'{key_for(_f, c)}.webp', 'WEBP',
                              quality=90, method=6)
                    written += 1
                print(f'  {start + len(batch):>4}/{len(rows)}')
    finally:
        httpd.shutdown()

    files = list(OUT.iterdir())
    if len(files) != len(rows):
        sys.exit(f'{written} renders but {len(files)} files — keys collided')
    size = sum(f.stat().st_size for f in files)
    print(f'\nwrote {len(files)} swatches to {OUT.relative_to(ROOT)} '
          f'({size / 1024 / 1024:.1f} MB)')


if __name__ == '__main__':
    main()
