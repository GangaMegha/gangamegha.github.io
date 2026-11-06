#!/usr/bin/env python3
"""Write the same navigation into every page, with correct relative paths.

Pages live at different depths, so the nav has to be generated rather than
copy-pasted. Run after adding or renaming a section or page.
"""
import re, os, glob, io

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

# Contact is deliberately not in the nav: every other item names a body of work
# and has its own page, while contact is an action. The email sits in the hero
# social row, the section stays at the bottom of the home page, and the footer
# carries the links on every page.
ITEMS = [("experience/","Experience"), ("publications/","Publications"), ("talks/","Talks"),
         ("writing/","Writing"), ("projects/","Projects"), ("education/","Education")]

def nav(pfx):
    links = "".join(
        '<a href="%s">%s</a>' % ((pfx + h) if (pfx or not h.startswith("#")) else h, label)
        for h, label in ITEMS)
    # The links sit in their own box so nav.js can move them into a panel when
    # they will not fit on one line. Search and the theme toggle stay put.
    return ('<div class="nav"><div class="nav-in"><a class="brand" href="%s">GangaMegha</a><nav>'
            '<div class="nlinks" id="navLinks">%s</div>'
            '<button class="searchbtn" id="searchBtn" aria-label="Search" title="Search (press /)">&#128269;</button>'
            '<button class="toggle" id="themeBtn" title="Switch theme" aria-label="Switch theme">'
            '<span class="tico">&#9728;</span><span class="tlabel">Light</span></button>'
            '<button class="burger" id="navBurger" aria-label="Menu" aria-expanded="false" aria-controls="navLinks">'
            '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg></button>'
            '</nav></div></div>'
            % (pfx or "/", links))

pages = ["index.html", "404.html"] + sorted(glob.glob("*/index.html")) \
        + sorted(glob.glob("projects/*/index.html"))
for f in pages:
    depth = f.count("/")
    pfx = "/" if f == "404.html" else "../" * depth
    s = io.open(f, encoding="utf-8").read()
    new, n = re.subn(r'<div class="nav">.*?</nav></div></div>', lambda m: nav(pfx), s,
                     count=1, flags=re.S)
    if n != 1:
        print("  !! no nav found in", f); continue
    tag = '<script src="%snav.js"></script>' % pfx
    if tag not in new:
        new = new.replace("</body>", tag + "\n</body>", 1)
    if new != s:
        io.open(f, "w", encoding="utf-8").write(new)
    print("  %-42s prefix=%r" % (f, pfx))
print("%d pages" % len(pages))
