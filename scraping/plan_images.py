#!/usr/bin/env python3
"""Pick the latest archived capture of every LT swatch image and emit a fetch list."""
import json, re, collections

def latest_by_url(path, pattern):
    """url -> (latest timestamp, original url) for urls matching pattern."""
    best = {}
    for r in json.load(open(path))[1:]:
        ts, url = r[1], r[2]
        m = re.search(pattern, url)
        if not m:
            continue
        code = m.group(1)
        if code not in best or ts > best[code][0]:
            best[code] = (ts, url)
    return best

thumbs = latest_by_url('cdx_img_swatches.json', r'/images/8801-(\d{4})\.jpg$')
large  = latest_by_url('cdx_img_uscom.json',    r'/images/lt_l_(\d{4})\.jpg$')
small  = latest_by_url('cdx_img_uscom.json',    r'/images/lt_(\d{4})\.jpg$')

sets = json.load(open('lt_snapshot_sets.json'))
codes = sorted({sku.split('-')[1] for sku in sets['20240805162934']['colors']})

print(f'{len(codes)} colours | thumbs {len(thumbs)} | large {len(large)} | uscom small {len(small)}')
missing_large = [c for c in codes if c not in large]
print('no large version:', missing_large)
print('no thumb:', [c for c in codes if c not in thumbs])

jobs = []
for c in codes:
    if c in thumbs:
        ts, u = thumbs[c]
        jobs.append(('thumb', c, ts, u))
    elif c in small:
        ts, u = small[c]
        jobs.append(('thumb', c, ts, u))
    if c in large:
        ts, u = large[c]
        jobs.append(('large', c, ts, u))
json.dump(jobs, open('image_jobs.json', 'w'), indent=1)
print('wrote', len(jobs), 'jobs')
