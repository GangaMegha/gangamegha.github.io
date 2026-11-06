#!/usr/bin/env python3
"""Swap the lettered placeholder tiles in the Experience timeline for logo images.

    python3 tools/set-logos.py            # use any files found in img/logos/
    python3 tools/set-logos.py --revert   # go back to lettered tiles

Looks for img/logos/<slug>.{svg,png,webp,jpg}. Slugs come from the data-logo
attribute on each placeholder, so adding a row to the timeline needs no change
here. Safe to run repeatedly.
"""
import os, re, sys, io

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
# (page, prefix to img/ from that page). The experience page carries the same
# tiles as the home timeline, so it has to be managed here too or its logos
# silently drift from the home page's.
PAGES = [("index.html", ""), ("experience/index.html", "../")]
LETTERS = {"amazon": "A", "microsoft": "M", "purdue": "P", "iitmadras": "I",
           "scancafe": "S"}

def find(slug):
    for ext in ("svg", "png", "webp", "jpg", "jpeg"):
        rel = "img/logos/%s.%s" % (slug, ext)
        if os.path.exists(rel):
            return rel
    return None

def run(page, pfx, revert, changed):
    s = io.open(page, encoding="utf-8").read()

    def to_img(m):
        slug = m.group(1)
        rel = find(slug)
        if revert or not rel:
            return m.group(0)
        changed.append((page, slug, rel))
        return ('<span class="tl-logo" data-logo="%s"><img src="%s%s" alt="" loading="lazy"></span>'
                % (slug, pfx, rel))

    def to_letter(m):
        slug = m.group(1)
        changed.append((slug, "letter"))
        return '<span class="tl-logo" data-logo="%s">%s</span>' % (slug, LETTERS.get(slug, slug[:1].upper()))

    # placeholder -> image
    s = re.sub(r'<span class="tl-logo" data-logo="([a-z0-9-]+)">[^<]*</span>', to_img, s)
    # image -> placeholder, when reverting or the file has gone away
    def maybe_back(m):
        slug, src = m.group(1), m.group(2)
        if revert or not os.path.exists(src[len(pfx):] if pfx and src.startswith(pfx) else src):
            changed.append((page, slug, "letter"))
            return '<span class="tl-logo" data-logo="%s">%s</span>' % (slug, LETTERS.get(slug, slug[:1].upper()))
        return m.group(0)
    s = re.sub(r'<span class="tl-logo" data-logo="([a-z0-9-]+)"><img src="([^"]+)"[^>]*></span>', maybe_back, s)

    io.open(page, "w", encoding="utf-8").write(s)

def main():
    revert = "--revert" in sys.argv
    changed = []
    for page, pfx in PAGES:
        if os.path.exists(page):
            run(page, pfx, revert, changed)
    if not changed:
        print("no change; add files to img/logos/ (see img/logos/README.md)")
    for page, slug, what in changed:
        print("  %-22s %-12s -> %s" % (page, slug, what))

main()
