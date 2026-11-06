#!/usr/bin/env python3
"""Regenerate search-data.js from the site's HTML.

Run from anywhere:   python3 tools/build-search-index.py

Indexes one document per item (each role, publication, talk, repo, project page)
rather than one per page, so a result points at something specific. Re-run this
after any content edit, or search will serve stale text.
"""
import re, os, json, html, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

def txt(s):
    s = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()

def read(p):
    return open(p, encoding="utf-8").read()

def chrome_stripped(s):
    """Page HTML minus nav, search overlay, footer and back-link."""
    s = re.sub(r'(?is)<div class="nav">.*?</nav></div></div>', " ", s)
    s = re.sub(r'(?is)<div class="sov".*?</body>', " ", s)
    s = re.sub(r'(?is)<p class="back">.*?</p>', " ", s)
    s = re.sub(r"(?is)<footer>.*?</footer>", " ", s)
    return s

def section_html(page, sid):
    m = re.search(r'(?is)<section[^>]*\bid="%s"[^>]*>(.*?)</section>' % re.escape(sid), page)
    return m.group(1) if m else ""

docs = []
seen = set()
def add(title, section, url, body):
    title, body = txt(title), txt(body)
    key = (title.lower(), url)
    if title and body and key not in seen:
        seen.add(key)
        docs.append({"title": title, "section": section, "url": url, "body": body})

def add_entries(scope, section, url):
    """One doc per <div class="entry">."""
    for block in re.split(r'(?i)<div class="entry">', scope)[1:]:
        h3 = re.search(r"(?is)<h3>(.*?)</h3>", block)
        if not h3:
            continue
        bits = [m.group(1) for m in
                (re.search(r'(?is)<div class="where">(.*?)</div>', block),
                 re.search(r'(?is)<span class="when">(.*?)</span>', block),
                 re.search(r'(?is)<p class="tags">(.*?)</p>', block))
                if m]
        bits += re.findall(r"(?is)<p>(.*?)</p>", block)
        add(h3.group(1), section, url, " ".join(bits))

def add_pubs(scope, section, url):
    for block in re.split(r'(?i)<div class="pub">', scope)[1:]:
        h3 = re.search(r"(?is)<h3>(.*?)</h3>", block)
        if h3:
            add(h3.group(1), section, url, " ".join(re.findall(r"(?is)<p[^>]*>(.*?)</p>", block)))

def add_items(scope, section, url):
    """One doc per <li> that leads with a <strong> label."""
    for li in re.findall(r"(?is)<li>(.*?)</li>", scope):
        st = re.search(r"(?is)<strong>(.*?)</strong>", li)
        if st and txt(li) != txt(st.group(1)):
            add(st.group(1).rstrip(". "), section, url, li)

# ---------------------------------------------------------------- home page
home = read("index.html")
add("Ganga Meghanath", "About", "/#about",
    " ".join(re.findall(r"(?is)<p[^>]*>(.*?)</p>", section_html(home, "about"))))
add_entries(section_html(home, "experience"), "Experience", "/experience/")
add_entries(section_html(home, "education"),  "Education",  "/education/")
add_pubs(chrome_stripped(read("publications/index.html")), "Publications", "/publications/")
add("Contact", "Contact", "/#contact", section_html(home, "contact"))

# ------------------------------------------------------------ inner pages
# The experience page lists an employer's roles together, then describes the
# whole tenure once, because the work does not split cleanly by job title.
# Index one document per ROLE so a search lands on a specific title, giving
# each the shared description plus its employer and location -- "Bing Ads"
# should be findable by "Bengaluru", and either Amazon role by "Bedrock".
exp = chrome_stripped(read("experience/index.html"))
for grp in re.split(r"(?i)<li><span class=\"tl-logo", exp)[1:]:
    emp = re.search(r'(?is)<h2 class="emp">(.*?)</h2>', grp)
    loc = re.search(r'(?is)<p class="eloc">(.*?)</p>', grp)
    # the work block now contains nested <div class="proj"> headers, so a
    # non-greedy match to the first </div> would swallow only the first one
    wrk = grp.split('<div class="work">', 1)[1] if '<div class="work">' in grp else None
    if not (emp and wrk):
        continue
    shared = " ".join([txt(wrk), txt(emp.group(1)), txt(loc.group(1)) if loc else ""])
    roles = re.search(r'(?is)<ul class="roles">(.*?)</ul>', grp)
    for li in re.findall(r"(?is)<li>(.*?)</li>", roles.group(1) if roles else ""):
        h3 = re.search(r"(?is)<h3>(.*?)</h3>", li)
        wn = re.search(r'(?is)<span class="when">(.*?)</span>', li)
        if h3:
            add(h3.group(1), "Experience", "/experience/",
                (txt(wn.group(1)) + " " if wn else "") + shared)

add_entries(chrome_stripped(read("talks/index.html")), "Talks",   "/talks/")
add_pubs(chrome_stripped(read("writing/index.html")),  "Writing", "/writing/")

edu = chrome_stripped(read("education/index.html"))
add_entries(edu, "Education", "/education/")
add_items(edu, "Education", "/education/")
courses = " ".join(re.findall(r'(?is)<ul class="plain cols">(.*?)</ul>', edu))
add("Academic coursework", "Education", "/education/", courses)

add_items(chrome_stripped(read("projects/index.html")), "Projects & code", "/projects/")

# -------------------------------------------------------- project detail
for f in sorted(glob.glob("projects/*/index.html")):
    s = read(f)
    h1 = re.search(r"(?is)<h1>(.*?)</h1>", s)
    if not h1:
        continue
    body = re.sub(r"(?is)<h1>.*?</h1>", " ", chrome_stripped(s))
    add(h1.group(1), "Projects", "/" + f.replace("index.html", ""), body)

# Two-way aliases: if a document contains either the acronym or the spelled-out
# phrase, the other is appended to its searchable body. Lets the visible page stay
# short while both spellings find it. Aliases are indexed only, never displayed.
# Only list pairs whose concept genuinely appears on the site -- this is for
# findability, not keyword stuffing.
SYNONYMS = [
    ("RAG", "retrieval-augmented generation"),
    ("LLM", "large language model"),
    ("DML", "double machine learning"),
    ("CWE", "common weakness enumeration"),
    ("IDOR", "insecure direct object reference"),
    ("A3C", "asynchronous advantage actor-critic"),
    ("NLP", "natural language processing"),
]

# Home-page tag lines describe an item in words its own page may never use
# (a project page can be NLP work without saying "NLP"). Fold each home tag
# into the document with the same title, wherever that document points.
by_title = {}
for d in docs:
    by_title.setdefault(d["title"].lower(), []).append(d)

for block in re.split(r'(?i)<div class="entry">', section_html(home, "projects"))[1:]:
    h3 = re.search(r"(?is)<h3>(.*?)</h3>", block)
    tg = re.search(r'(?is)<p class="tags">(.*?)</p>', block)
    if h3 and tg:
        for d in by_title.get(txt(h3.group(1)).lower(), []):
            if txt(tg.group(1)).lower() not in d["body"].lower():
                d["body"] += " " + txt(tg.group(1))

# Words a reader is likely to type that do not appear in the items themselves.
SECTION_TERMS = {
    "Publications": "paper papers publication peer-reviewed journal research",
    "Writing": "article articles blog blog post Medium",
    "Talks":   "talk talks poster presentation conference workshop",
}

def present(needle, hay):
    return re.search(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(needle.lower()),
                     hay, re.I) is not None

for d in docs:
    hay = d["title"] + " " + d["body"]
    extra = []
    for short, long in SYNONYMS:
        has_s, has_l = present(short, hay), present(long, hay)
        if has_s and not has_l:
            extra.append(long)
        elif has_l and not has_s:
            extra.append(short)
    extra.append(SECTION_TERMS.get(d["section"], ""))
    extra = [e for e in extra if e]
    if extra:
        d["body"] += " " + " ".join(extra)

out = "window.SEARCH_DATA=" + json.dumps(docs, ensure_ascii=False, separators=(",", ":")) + ";\n"
open("search-data.js", "w", encoding="utf-8").write(out)
print("indexed %d documents -> search-data.js (%d bytes)" % (len(docs), len(out)))
for d in docs:
    print("   %-10s %-22s %s" % (d["section"][:10], d["url"][:22], d["title"][:58]))
