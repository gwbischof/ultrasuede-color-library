#!/usr/bin/env python3
"""Extract '<code> <Color Name>' pairs from an Ultrasuede color-card PDF.

The cards embed their colour legend as one long text run, e.g.
"...6564 Fuchsia6581 OpalStyle: 8801Note: We have made every effort...".
We therefore split on the 4-digit codes rather than trying to match names.
"""
import zlib, re, sys

# text that can follow the final colour name on a card
TRAILERS = ('Style', 'ultrasuede', 'Note', 'FUNDAMENTALS', 'SPECIFICATIONS')


def raw_text(path):
    d = open(path, 'rb').read()
    out = []
    for m in re.finditer(rb'stream\r?\n(.*?)endstream', d, re.S):
        try:
            s = zlib.decompress(m.group(1))
        except Exception:
            continue
        out.append(b''.join(re.findall(rb'\(((?:\\.|[^\\()])*)\)', s)))
    return re.sub(r'\\\d{3}', '', b' '.join(out).decode('latin1'))


def colors(path):
    t = raw_text(path)
    hits = list(re.finditer(r'(?<!\d)(\d{4})(?=[A-Z\s])', t))
    out = []
    for i, m in enumerate(hits):
        end = hits[i + 1].start() if i + 1 < len(hits) else len(t)
        name = t[m.end():end]
        for tr in TRAILERS:                       # cut trailing prose
            name = name.split(tr)[0]
        name = name.strip(' \t\r\n:')
        if name and re.fullmatch(r"[A-Za-z][A-Za-z'\- ]{1,24}", name):
            out.append((m.group(1), name))
    # de-dup, keep first occurrence
    seen, uniq = set(), []
    for c, n in out:
        if c not in seen:
            seen.add(c); uniq.append((c, n))
    return uniq


def style_number(path):
    m = re.search(r'Style:?\s*(\d{3,4})', raw_text(path))
    return m.group(1) if m else None


if __name__ == '__main__':
    for p in sys.argv[1:]:
        c = colors(p)
        print(f'\n== {p}  style {style_number(p)}  ({len(c)} colors)')
        for code, name in c:
            print(f'   {code}  {name}')
