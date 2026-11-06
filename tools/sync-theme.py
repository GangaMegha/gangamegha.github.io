#!/usr/bin/env python3
"""Regenerate the prefers-color-scheme block from the :root[data-theme="light"] block.

The two must hold identical values: one serves visitors who clicked the toggle,
the other serves visitors who have not chosen and whose system is set to light.
CSS cannot share one declaration across a media query, so this keeps the copy
honest. Run after editing any light-theme colour.

    python3 tools/sync-theme.py           # rewrite the generated block
    python3 tools/sync-theme.py --check   # exit 1 if they have drifted
"""
import re, sys, io, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = os.path.join(ROOT, "style.css")
MARK = "/* No explicit choice yet"

def main():
    check = "--check" in sys.argv
    c = io.open(CSS, encoding="utf-8").read()
    src = re.search(r':root\[data-theme="light"\]\{(.*?)\n\}', c, re.S)
    if not src:
        sys.exit("could not find the light-theme block")
    body = src.group(1)
    block = ('\n\n' + MARK + ": follow the visitor's system setting. An explicit\n"
             "   choice sets data-theme and wins over this. Generated from the block above\n"
             "   by tools/sync-theme.py -- edit the light values there, not here. */\n"
             '@media (prefers-color-scheme: light){\n'
             ' :root:not([data-theme="dark"]){%s\n }\n}' % body.replace("\n", "\n "))
    existing = re.search(r'\n\n/\* No explicit choice yet.*?\n[ \t]*\}\n\}', c, re.S)
    if check:
        if not existing or existing.group(0) != block:
            print("DRIFT: the generated block no longer matches the light theme.")
            print("Run: python3 tools/sync-theme.py")
            sys.exit(1)
        print("theme blocks are in sync")
        return
    c = c.replace(existing.group(0), "") if existing else c
    src = re.search(r':root\[data-theme="light"\]\{.*?\n\}', c, re.S)
    io.open(CSS, "w", encoding="utf-8").write(c.replace(src.group(0), src.group(0) + block, 1))
    print("regenerated the system-preference block")

main()
