#!/usr/bin/env python3
"""Write the same footer into every page, with correct relative paths.

Mirrors tools/set-nav.py. The profile links live here rather than in the
Contact section so they appear on all pages, not just the home page.
Run after changing a profile link or the "last updated" date.
"""
import re, os, glob, io

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

UPDATED = "Last updated November 2026."

# (href, label, needs_prefix)
LINKS = [
    ("https://www.linkedin.com/in/gangamegha/", "LinkedIn", False),
    ("https://scholar.google.com/citations?user=Qn7cHcYAAAAJ&amp;hl=en", "Google Scholar", False),
    ("https://github.com/GangaMegha", "GitHub", False),
    ("https://medium.com/@ganga_megha", "Medium", False),
    ("files/CV.pdf", "CV (PDF)", True),
]

def footer(pfx):
    links = "".join('<a href="%s">%s</a>' % ((pfx + h) if needs else h, label)
                    for h, label, needs in LINKS)
    return ('<footer><div class="foot-in"><p class="flinks">%s</p>'
            '<p class="fupd">%s</p></div></footer>' % (links, UPDATED))

pages = ["index.html", "404.html"] + sorted(glob.glob("*/index.html")) \
        + sorted(glob.glob("projects/*/index.html"))
changed = 0
for f in pages:
    depth = f.count("/")
    pfx = "/" if f == "404.html" else "../" * depth
    s = io.open(f, encoding="utf-8").read()
    new, n = re.subn(r"<footer>.*?</footer>", lambda m: footer(pfx), s, count=1, flags=re.S)
    if n != 1:
        print("  !! no footer found in", f); continue
    if new != s:
        io.open(f, "w", encoding="utf-8").write(new); changed += 1
    print("  %-42s prefix=%r" % (f, pfx))
print("%d pages, %d changed" % (len(pages), changed))
