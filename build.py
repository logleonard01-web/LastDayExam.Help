#!/usr/bin/env python3
"""Static site generator for Last Day Exam Help.

Reads content/*.md (articles), content/glossary.txt and content/practice.txt,
writes the finished site into ./site. No third-party dependencies.

Run:  python3 build.py
"""
import glob
import html
import json
import os
import re
import shutil
import sys
import datetime

# ------------------------------------------------------------------ config
SITE = "https://lastdayexam.help"
BRAND = "Last Day Exam Help"
TAGLINE = "Understand more. Revise smarter. Make your study time count."
OUT = "site"
PUBLISHED = "2026-10-21"          # fixed so the date never changes on rebuild
CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "")   # set before launch
# Keep the site out of search engines until real contact details are set.
NOINDEX = os.environ.get("NOINDEX", "" if CONTACT_EMAIL else "1") == "1"
AI_DISCLOSURE = True
e = html.escape

SUBJECTS = {
    "mathematics": ("Mathematics", "Arithmetic, algebra, geometry, statistics and probability.", ["Mathematics"]),
    "science": ("Science", "Biology, chemistry, physics and the scientific method.", ["Biology", "Chemistry", "Physics", "Scientific method"]),
    "english": ("English", "Writing, grammar, vocabulary and figurative language.", ["English"]),
    "history": ("History and Geography", "Sources, causation, maps and coordinates.", ["History and geography"]),
    "computer-science": ("Computer Science", "Algorithms, programming concepts and data types.", ["Computer science"]),
    "economics": ("Economics", "Markets, scarcity, inflation and opportunity cost.", ["Economics"]),
    "research-writing": ("Research and Academic Writing", "Sources, citations and avoiding plagiarism.", ["Research"]),
    "critical-thinking": ("Critical Thinking", "Reasoning, evidence, correlation and fallacies.", ["Critical thinking"]),
}
OTHER_HUBS = {
    "exam-prep": ("Exam Preparation", "/exam-preparation/", "Plans, checklists and strategies for the days before an exam."),
    "study-skills": ("Study Skills", "/study-skills/", "Habits and techniques that make revision more effective."),
}
SUBJ_LABEL = {k: v[0] for k, v in SUBJECTS.items()}
SUBJ_LABEL.update({k: v[0] for k, v in OTHER_HUBS.items()})
PRACTICE_LABEL = dict(SUBJ_LABEL)

NAV = [("/", "Home"), ("/subjects/", "Subjects"), ("/exam-preparation/", "Exam Preparation"),
       ("/quick-revision/", "Quick Revision"), ("/vocabulary/", "Academic Vocabulary"),
       ("/practice/", "Practice Questions"), ("/study-skills/", "Study Skills"),
       ("/blog/", "Blog"), ("/about/", "About")]

ERRORS = []


def err(msg):
    ERRORS.append(msg)


# ------------------------------------------------------------------ helpers
def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def write(path, content):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


def inline(text):
    text = e(text, quote=False)
    codes = []

    def keep(m):
        codes.append(m.group(1))
        return "\x00%d\x00" % (len(codes) - 1)

    text = re.sub(r"`([^`]+)`", keep, text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", text)
    text = re.sub(r"\x00(\d+)\x00", lambda m: "<code>%s</code>" % codes[int(m.group(1))], text)
    return text


LIST_RE = re.compile(r"^(\s*)([-*]|\d+\.)\s+(.*)$")


def is_block_start(line):
    return (line.startswith("#") or line.startswith("|") or line.startswith("```")
            or bool(LIST_RE.match(line)))


def md(text):
    """Small Markdown converter. Returns (html, [h2 headings])."""
    lines = text.strip("\n").split("\n")
    out, heads, i = [], [], 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
        elif line.startswith("```"):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append("<pre><code>%s</code></pre>" % e("\n".join(buf)))
        elif line.startswith("### "):
            out.append("<h3>%s</h3>" % inline(line[4:]))
            i += 1
        elif line.startswith("## "):
            t = line[3:].strip()
            heads.append(t)
            out.append('<h2 id="%s">%s</h2>' % (slugify(t), inline(t)))
            i += 1
        elif line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|?$", lines[i + 1]):
            def cells(r):
                return [c.strip() for c in r.strip().strip("|").split("|")]
            head = cells(line)
            i += 2
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(cells(lines[i]))
                i += 1
            t = "<div class=\"table-wrap\"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>" % (
                "".join("<th scope=\"col\">%s</th>" % inline(c) for c in head),
                "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c) for c in r) for r in rows))
            out.append(t)
        elif LIST_RE.match(line):
            items = []  # (indent, marker, text)
            while i < len(lines) and LIST_RE.match(lines[i]):
                m = LIST_RE.match(lines[i])
                items.append((len(m.group(1)), m.group(2), m.group(3)))
                i += 1
            ordered = items[0][1][0].isdigit()
            tag = "ol" if ordered else "ul"
            parts = []
            k = 0
            while k < len(items):
                ind, mk, tx = items[k]
                sub = []
                k += 1
                while k < len(items) and items[k][0] > ind:
                    sub.append(items[k][2])
                    k += 1
                li = inline(tx)
                if sub:
                    li += "<ul>%s</ul>" % "".join("<li>%s</li>" % inline(s) for s in sub)
                parts.append("<li>%s</li>" % li)
            out.append("<%s>%s</%s>" % (tag, "".join(parts), tag))
        else:
            buf = []
            while i < len(lines) and lines[i].strip() and not (buf and is_block_start(lines[i])):
                buf.append(lines[i].strip())
                i += 1
            out.append("<p>%s</p>" % inline(" ".join(buf)))
    return "\n".join(out), heads


# ------------------------------------------------------------------ load content
def load_articles():
    arts = []
    for f in sorted(glob.glob("content/*.md")):
        raw = open(f, encoding="utf-8").read()
        for chunk in re.split(r"(?m)^=== ", raw)[1:]:
            slug, rest = chunk.split("\n", 1)
            head, body = rest.split("\n---\n", 1)
            meta = {"slug": slug.strip(), "body": body.strip()}
            for ln in head.strip().split("\n"):
                k, v = ln.split(":", 1)
                meta[k.strip()] = v.strip()
            for k in ("vocab", "related"):
                meta[k] = [x.strip() for x in meta.get(k, "").split(",") if x.strip()]
            meta["words"] = len(re.findall(r"\w+", body))
            arts.append(meta)
    return arts


def load_glossary():
    terms = {}
    for ln in open("content/glossary.txt", encoding="utf-8"):
        ln = ln.rstrip("\n")
        if not ln or ln.startswith("#"):
            continue
        p = ln.split("|")
        if len(p) != 9:
            err("glossary line has %d fields: %s" % (len(p), ln[:50]))
            continue
        slug, term, pos, subj, defn, exp, ex, conf, rel = p
        if slug in terms:
            err("duplicate glossary slug " + slug)
        terms[slug] = dict(slug=slug, term=term, pos=pos, subject=subj, defn=defn, exp=exp, ex=ex, conf=conf,
                           related=[x.strip() for x in rel.split(",") if x.strip()])
    return terms


def load_practice():
    qs = []
    for ln in open("content/practice.txt", encoding="utf-8"):
        ln = ln.rstrip("\n")
        if not ln or ln.startswith("#"):
            continue
        p = ln.split("|")
        if len(p) != 9:
            err("practice line has %d fields: %s" % (len(p), ln[:50]))
            continue
        qid, subj, diff, topic, q, opts, ans, why, mis = p
        options = [o for o in opts.split(";;") if o] if opts else []
        if options and ans not in options:
            err("practice %s: answer not among options" % qid)
        qs.append(dict(id=qid, subject=subj, diff=diff, topic=topic, q=q, options=options, ans=ans, why=why, mis=mis))
    return qs


ARTICLES = load_articles()
TERMS = load_glossary()
PRACTICE = load_practice()
BY_SLUG = {a["slug"]: a for a in ARTICLES}
PAGES = []     # (url, lastmod)
SEARCH = []    # search index entries


# ------------------------------------------------------------------ validation of content references
for a in ARTICLES:
    for k in ("slug", "title", "subject", "kind", "description"):
        if k not in a:
            err("article missing %s: %s" % (k, a.get("slug")))
    if a["subject"] not in SUBJ_LABEL:
        err("unknown subject %s in %s" % (a["subject"], a["slug"]))
    for v in a["vocab"]:
        if v not in TERMS:
            err("article %s references unknown term %s" % (a["slug"], v))
    for r in a["related"]:
        if r not in BY_SLUG:
            err("article %s references unknown article %s" % (a["slug"], r))
    if a.get("practice") and a["practice"] not in PRACTICE_LABEL:
        err("article %s unknown practice subject %s" % (a["slug"], a["practice"]))
for t in TERMS.values():
    for r in t["related"]:
        if r not in TERMS:
            err("term %s references unknown term %s" % (t["slug"], r))
for q in PRACTICE:
    if q["subject"] not in PRACTICE_LABEL:
        err("practice %s unknown subject %s" % (q["id"], q["subject"]))

# reverse index: term -> articles
TERM_ARTICLES = {s: [] for s in TERMS}
for a in ARTICLES:
    for v in a["vocab"]:
        if v in TERM_ARTICLES:
            TERM_ARTICLES[v].append(a["slug"])
for s, t in TERMS.items():
    if t["subject"] == "Command words" and "exam-command-words" not in TERM_ARTICLES[s]:
        TERM_ARTICLES[s].append("exam-command-words")


# ------------------------------------------------------------------ layout
def card_list(items):
    return '<ul class="cards">' + "".join(
        '<li><a href="%s"><strong>%s</strong></a><span>%s</span></li>' % (u, e(t), e(d)) for u, t, d in items) + "</ul>"


def layout(url, title, desc, body, crumbs=None, jsonld="", noindex=False, article=False):
    full_title = title if url == "/" else "%s | %s" % (title, BRAND)
    nav = "".join('<li><a href="%s"%s>%s</a></li>' % (u, ' aria-current="page"' if u == url else "", t) for u, t in NAV)
    bc = ""
    if crumbs:
        items = [("/", "Home")] + crumbs
        bc = ('<nav aria-label="Breadcrumb" class="crumbs"><ol>' +
              "".join('<li><a href="%s">%s</a></li>' % (u, e(t)) for u, t in items[:-1]) +
              '<li aria-current="page">%s</li></ol></nav>' % e(items[-1][1]))
        ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": t, "item": SITE + u} for i, (u, t) in enumerate(items)]}
        jsonld += '<script type="application/ld+json">%s</script>' % json.dumps(ld)
    robots = '<meta name="robots" content="noindex, follow">' if (NOINDEX or noindex) else ""
    og = ('<meta property="og:title" content="%s"><meta property="og:description" content="%s">'
          '<meta property="og:type" content="%s"><meta property="og:url" content="%s%s"><meta property="og:site_name" content="%s">'
          % (e(full_title), e(desc), "article" if article else "website", SITE, url, BRAND))
    ai = ""
    if AI_DISCLOSURE:
        ai = " Some content is drafted with AI assistance and edited by the editorial team; see <a href=\"/editorial-standards/\">editorial standards</a>."
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title><meta name="description" content="%s">
<link rel="canonical" href="%s%s">%s%s
<meta name="theme-color" content="#1d4ed8">
<link rel="alternate" type="application/rss+xml" title="%s" href="/rss.xml">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/style.css">%s
<script>document.documentElement.className='js'</script></head>
<body><a class="skip" href="#main">Skip to content</a>
<header class="site-header"><div class="wrap head-row"><a class="brand" href="/">%s</a>
<form class="search" role="search" action="/search/" method="get"><label for="q" class="sr">Search articles, subjects and vocabulary</label>
<input id="q" name="q" type="search" placeholder="Search terms, subjects, formulas" autocomplete="off"><button type="submit">Search</button></form>
<button class="menu-btn" type="button" aria-expanded="false" aria-controls="nav-list">Menu</button></div>
<nav aria-label="Main" class="wrap"><ul class="nav" id="nav-list">%s</ul></nav></header>
<main id="main" class="wrap">%s%s</main>
<footer class="site-footer"><div class="wrap"><p><strong>%s</strong><br>%s</p>
<p><a href="/about/">About</a> · <a href="/contact/">Contact</a> · <a href="/editorial-standards/">Editorial standards</a> ·
<a href="/corrections/">Corrections</a> · <a href="/privacy/">Privacy</a> · <a href="/terms/">Terms</a> ·
<a href="/accessibility/">Accessibility</a> · <a href="/rss.xml">RSS</a></p>
<p class="small">&copy; %d %s. Educational information only; it does not guarantee any exam result.%s</p></div></footer>
<script src="/assets/site.js" defer></script></body></html>""" % (
        e(full_title), e(desc), SITE, url, robots, og, BRAND, jsonld, BRAND, nav, bc, body, BRAND, e(TAGLINE),
        datetime.date.today().year, BRAND, ai)


def page(url, title, desc, body, crumbs=None, kind="Page", sitemap=True, search=True, keywords="", **kw):
    path = "index.html" if url == "/" else url.strip("/") + "/index.html"
    write(path, layout(url, title, desc, body, crumbs, **kw))
    if sitemap:
        PAGES.append(url)
    if search:
        SEARCH.append({"t": title, "u": url, "d": desc, "k": kind, "h": keywords})


def article_link(slug):
    a = BY_SLUG[slug]
    return ("/blog/%s/" % slug, a["title"], a["kind"])


# ------------------------------------------------------------------ vocabulary pages
def term_card(slug):
    t = TERMS[slug]
    return ("/vocabulary/%s/" % slug, t["term"], t["defn"])


def build_vocab():
    letters = {}
    for s, t in TERMS.items():
        letters.setdefault(t["term"][0].upper(), []).append(s)
    subj_list = sorted({t["subject"] for t in TERMS.values()})
    az = " ".join('<a href="#letter-%s">%s</a>' % (l, l) for l in sorted(letters))
    body = ("<h1>Academic Vocabulary</h1><p>%d terms, from exam command words to subject vocabulary. Search, filter by subject or "
            "browse alphabetically. Each entry links to related terms and study guides.</p>" % len(TERMS))
    body += ('<div class="filters"><label for="vq">Find a term</label> <input id="vq" type="search" data-vocab-q autocomplete="off"> '
             '<label for="vs">Subject</label> <select id="vs" data-vocab-s><option value="">All subjects</option>%s</select></div>'
             '<p class="az" aria-label="Alphabetical index">%s</p>'
             '<p id="vocab-status" role="status" aria-live="polite" class="small"></p>'
             % ("".join("<option>%s</option>" % e(x) for x in subj_list), az))
    for l in sorted(letters):
        body += '<section class="letter" data-letter><h2 id="letter-%s">%s</h2><ul class="cards">' % (l, l)
        for s in sorted(letters[l], key=lambda x: TERMS[x]["term"].lower()):
            t = TERMS[s]
            body += ('<li data-subject="%s" data-text="%s"><a href="/vocabulary/%s/"><strong>%s</strong></a><span>%s</span><em class="tag">%s</em></li>'
                     % (e(t["subject"]), e((t["term"] + " " + t["defn"]).lower()), s, e(t["term"]), e(t["defn"]), e(t["subject"])))
        body += "</ul></section>"
    body += '<p id="vocab-empty" class="notice" hidden>No terms match. Try a shorter word, remove the subject filter, or use the site <a href="/search/">search</a>.</p>'
    page("/vocabulary/", "Academic Vocabulary", "Searchable glossary of academic terms and exam command words with definitions and examples.",
         body, crumbs=[("/vocabulary/", "Academic Vocabulary")], kind="Vocabulary")

    for s, t in TERMS.items():
        b = '<article><h1>%s</h1><p class="meta"><em>%s</em> · %s</p>' % (e(t["term"]), e(t["pos"]), e(t["subject"]))
        b += "<h2>Definition</h2><p>%s</p><h2>Explanation</h2><p>%s</p><h2>Example</h2><p>%s</p>" % (e(t["defn"]), e(t["exp"]), e(t["ex"]))
        if t["subject"] == "Command words":
            b += ("<h2>In an exam</h2><p>Command-word meanings can vary between subjects, exam boards and mark schemes, so check your own board's "
                  "guidance. See <a href=\"/blog/exam-command-words/\">Exam Command Words: What Each Instruction Asks For</a>.</p>")
        b += "<h2>Common confusion</h2><p>%s</p></article>" % e(t["conf"])
        if t["related"]:
            b += "<h2>Related terms</h2>" + card_list([term_card(r) for r in t["related"]])
        arts = TERM_ARTICLES.get(s, [])
        if arts:
            b += "<h2>Study guides that use this term</h2>" + card_list([article_link(x) for x in arts])
        b += ('<p class="small">Entry status: written by the editorial team and awaiting independent review. '
              'Spot an error? Use our <a href="/corrections/">corrections page</a>.</p>')
        b += '<p><a href="/vocabulary/">&larr; All vocabulary</a></p>'
        page("/vocabulary/%s/" % s, t["term"], t["defn"], b,
             crumbs=[("/vocabulary/", "Academic Vocabulary"), ("/vocabulary/%s/" % s, t["term"])], kind="Vocabulary",
             keywords=t["subject"])


# ------------------------------------------------------------------ practice pages
def render_question(n, q):
    h = '<article class="q"><h3>Question %d</h3><p class="meta">%s · %s · %s</p><p>%s</p>' % (
        n, e(PRACTICE_LABEL[q["subject"]]), e(q["topic"]), e(q["diff"]), e(q["q"]))
    if q["options"]:
        h += "<ul class=\"opts\">" + "".join("<li>%s. %s</li>" % ("ABCDEF"[i], e(o)) for i, o in enumerate(q["options"])) + "</ul>"
    h += ("<details><summary>Show answer and explanation</summary><p><strong>Answer:</strong> %s</p><p>%s</p>"
          "<p><strong>Common misconception:</strong> %s</p></details></article>" % (e(q["ans"]), e(q["why"]), e(q["mis"])))
    return h


def build_practice():
    subs = [s for s in PRACTICE_LABEL if any(q["subject"] == s for q in PRACTICE)]
    body = ("<h1>Practice Questions</h1><p>%d original practice questions with checked answers and explanations. They are written for "
            "this site and are not official exam content. Try each question before opening the answer.</p>" % len(PRACTICE))
    body += card_list([("/practice/%s/" % s, PRACTICE_LABEL[s], "%d questions" % sum(1 for q in PRACTICE if q["subject"] == s)) for s in subs])
    page("/practice/", "Practice Questions", "Original practice questions with explained answers across mathematics, science, English and more.",
         body, crumbs=[("/practice/", "Practice Questions")], kind="Practice")
    for s in subs:
        qs = [q for q in PRACTICE if q["subject"] == s]
        b = "<h1>%s Practice Questions</h1><p>%d questions. Work each one out before revealing the answer.</p>" % (e(PRACTICE_LABEL[s]), len(qs))
        b += "".join(render_question(i + 1, q) for i, q in enumerate(qs))
        guides = [article_link(a["slug"]) for a in ARTICLES if a["subject"] == s][:4]
        if guides:
            b += "<h2>Study guides</h2>" + card_list(guides)
        page("/practice/%s/" % s, "%s Practice Questions" % PRACTICE_LABEL[s],
             "Original %s practice questions with explained answers." % PRACTICE_LABEL[s].lower(), b,
             crumbs=[("/practice/", "Practice Questions"), ("/practice/%s/" % s, PRACTICE_LABEL[s])], kind="Practice")
    return subs


# ------------------------------------------------------------------ articles
def words_to_minutes(n):
    return max(1, round(n / 200.0))


def build_articles(practice_subjects):
    for a in ARTICLES:
        s = a["slug"]
        body_html, heads = md(a["body"])
        toc = ""
        if len(heads) >= 3:
            toc = '<nav class="toc" aria-label="On this page"><strong>On this page</strong><ul>%s</ul></nav>' % "".join(
                '<li><a href="#%s">%s</a></li>' % (slugify(h), e(h)) for h in heads)
        hub_url = ("/subjects/%s/" % a["subject"]) if a["subject"] in SUBJECTS else OTHER_HUBS[a["subject"]][1]
        label = SUBJ_LABEL[a["subject"]]
        b = '<article><h1>%s</h1><p class="meta">%s · %s · %d min read</p>' % (e(a["title"]), e(a["kind"]), e(label), words_to_minutes(a["words"]))
        b += '<p class="lead">%s</p>%s%s</article>' % (e(a["description"]), toc, body_html)
        if a["vocab"]:
            b += "<h2>Key vocabulary</h2>" + card_list([term_card(v) for v in a["vocab"]])
        rel = [article_link(r) for r in a["related"]]
        same = [article_link(x["slug"]) for x in ARTICLES if x["subject"] == a["subject"] and x["slug"] != s and x["slug"] not in a["related"]]
        rel = (rel + same)[:5]
        if rel:
            b += "<h2>Keep learning</h2>" + card_list(rel)
        extra = '<a href="%s">%s hub</a>' % (hub_url, e(label))
        if a.get("practice") in practice_subjects:
            extra += ' · <a href="/practice/%s/">%s practice questions</a>' % (a["practice"], e(PRACTICE_LABEL[a["practice"]]))
        b += "<p>More: %s</p>" % extra
        b += ('<aside class="about-box"><strong>About this article</strong><br>Published %s. Last updated %s. Written by the %s editorial team. '
              'Status: awaiting independent review. This guide is general educational information; check your own exam board or teacher for '
              'requirements that apply to you. Found a mistake? <a href="/corrections/">Tell us</a>.</aside>' % (PUBLISHED, PUBLISHED, BRAND))
        ld = '<script type="application/ld+json">%s</script>' % json.dumps({
            "@context": "https://schema.org", "@type": "Article", "headline": a["title"], "description": a["description"],
            "datePublished": PUBLISHED, "dateModified": PUBLISHED, "mainEntityOfPage": "%s/blog/%s/" % (SITE, s),
            "author": {"@type": "Organization", "name": BRAND, "url": SITE + "/"},
            "publisher": {"@type": "Organization", "name": BRAND, "url": SITE + "/"}})
        page("/blog/%s/" % s, a["title"], a["description"], b,
             crumbs=[("/blog/", "Blog"), ("/blog/%s/" % s, a["title"])], kind="Article", jsonld=ld, article=True,
             keywords=label + " " + " ".join(heads))


# ------------------------------------------------------------------ hubs and index pages
def build_hubs():
    # subjects
    page("/subjects/", "Subjects", "Browse study guides, vocabulary and practice questions by subject.",
         "<h1>Subjects</h1><p>Choose a subject to find guides, key vocabulary and practice questions.</p>" +
         card_list([("/subjects/%s/" % k, v[0], v[1]) for k, v in SUBJECTS.items()]),
         crumbs=[("/subjects/", "Subjects")], kind="Subject")
    psubs = {q["subject"] for q in PRACTICE}
    for k, (name, desc, vsubs) in SUBJECTS.items():
        arts = [a for a in ARTICLES if a["subject"] == k]
        vocab = [s for s, t in TERMS.items() if t["subject"] in vsubs]
        b = "<h1>%s</h1><p>%s</p>" % (e(name), e(desc))
        b += "<h2>Study guides</h2>" + card_list([article_link(a["slug"]) for a in arts])
        if vocab:
            b += "<h2>Key vocabulary</h2>" + card_list([term_card(v) for v in sorted(vocab, key=lambda x: TERMS[x]["term"].lower())])
        if k in psubs:
            b += '<h2>Practice</h2><p><a href="/practice/%s/">%s practice questions</a></p>' % (k, e(name))
        page("/subjects/%s/" % k, name, desc, b, crumbs=[("/subjects/", "Subjects"), ("/subjects/%s/" % k, name)], kind="Subject")
    # exam prep and study skills
    for k, (name, url, desc) in OTHER_HUBS.items():
        arts = [a for a in ARTICLES if a["subject"] == k]
        extra = ""
        if k == "exam-prep":
            extra = ("<h2>Principles</h2><ul><li>Review and organise. Do not try to learn an entire subject overnight.</li>"
                     "<li>Protect sleep and take breaks.</li><li>Spend most time on topics that are important and shaky.</li>"
                     "<li>Use <a href=\"/vocabulary/\">command-word definitions</a> to read questions correctly.</li></ul>")
        b = "<h1>%s</h1><p>%s</p>%s%s" % (e(name), e(desc), card_list([article_link(a["slug"]) for a in arts]), extra)
        page(url, name, desc, b, crumbs=[(url, name)], kind="Hub")
    # quick revision
    qr = [a for a in ARTICLES if a["kind"] in ("Quick revision", "Revision checklist", "Worked example", "Cornerstone guide")]
    b = ("<h1>Quick Revision</h1><p>Condensed guides with the key concept, essential vocabulary, formulas, a worked example, common mistakes "
         "and a recap. Each guide uses only the sections that suit its subject.</p>")
    for kind in ("Quick revision", "Revision checklist", "Worked example", "Cornerstone guide"):
        g = [a for a in qr if a["kind"] == kind]
        if g:
            b += "<h2>%s%s</h2>" % (e(kind), "s" if not kind.endswith("t") else "") + card_list([article_link(a["slug"]) for a in g])
    page("/quick-revision/", "Quick Revision", "Quick revision guides, worked examples and checklists for limited study time.", b,
         crumbs=[("/quick-revision/", "Quick Revision")], kind="Hub")
    # blog archive grouped by subject
    b = "<h1>Blog</h1><p>%d study guides and explainers. Jump to: %s</p>" % (
        len(ARTICLES), " · ".join('<a href="#s-%s">%s</a>' % (k, e(SUBJ_LABEL[k])) for k in SUBJ_LABEL if any(a["subject"] == k for a in ARTICLES)))
    for k in SUBJ_LABEL:
        arts = [a for a in ARTICLES if a["subject"] == k]
        if arts:
            b += '<h2 id="s-%s">%s</h2>' % (k, e(SUBJ_LABEL[k])) + card_list([article_link(a["slug"]) for a in arts])
    page("/blog/", "Blog", "Study guides, explainers and revision articles across all subjects.", b,
         crumbs=[("/blog/", "Blog")], kind="Hub")


def build_home(practice_subjects):
    corner = [a for a in ARTICLES if a["kind"] == "Cornerstone guide"]
    cmd = ["analyze", "evaluate", "compare", "explain", "describe", "justify"]
    b = ('<section class="hero"><h1>%s</h1><p class="lead">%s</p>'
         '<p>Clear explanations, an academic vocabulary library, quick-revision guides and original practice questions for when study time is limited. '
         'Last-minute revision works best as a way to review, organise and strengthen what you already know.</p>'
         '<p><a class="btn" href="/blog/final-day-exam-plan/">Plan your final day</a> <a class="btn alt" href="/vocabulary/">Browse vocabulary</a> '
         '<a class="btn alt" href="/practice/">Practise</a></p></section>' % (BRAND, e(TAGLINE)))
    b += "<h2>Subjects</h2>" + card_list([("/subjects/%s/" % k, v[0], v[1]) for k, v in SUBJECTS.items()])
    b += "<h2>Start here</h2>" + card_list([article_link(a["slug"]) for a in corner])
    b += "<h2>Exam command words</h2><p>Know what the question is asking before you answer. <a href=\"/blog/exam-command-words/\">Read the full guide</a>.</p>"
    b += card_list([term_card(c) for c in cmd])
    b += "<h2>Latest guides</h2>" + card_list([article_link(a["slug"]) for a in ARTICLES[-6:]])
    page("/", BRAND, "Educational resources for exam preparation: explanations, vocabulary, revision guides and practice questions.", b,
         kind="Home", search=False)


def build_trust():
    def simple(url, title, desc, body):
        page(url, title, desc, "<h1>%s</h1>%s" % (title, body), crumbs=[(url, title)], kind="Page", search=True)

    simple("/about/", "About", "About Last Day Exam Help.",
           "<p>%s helps students understand academic concepts, prepare for exams and learn the vocabulary they need, especially when study time is limited.</p>"
           "<p>Our mission is to make difficult concepts easier to understand. We publish study guides, a growing academic vocabulary library, "
           "quick-revision guides and original practice questions.</p>"
           "<h2>What we do not claim</h2><p>We do not promise exam results, and we do not suggest that a subject can be mastered overnight. "
           "Last-minute revision is a way to review, organise and strengthen knowledge you already have.</p>"
           "<h2>Who it is for</h2><p>Students preparing for exams, plus teachers, parents, homeschoolers and independent learners.</p>"
           "<p>See our <a href=\"/editorial-standards/\">editorial standards</a> for how content is written and corrected.</p>" % BRAND)
    if CONTACT_EMAIL:
        contact = '<p>Email us at <a href="mailto:%s">%s</a>. Please include the page address if you are reporting an error.</p>' % (e(CONTACT_EMAIL), e(CONTACT_EMAIL))
    else:
        contact = ('<p>Contact details will be published here before the site is opened to search engines. '
                   'Site owner: set the <code>CONTACT_EMAIL</code> value in the build and rebuild.</p>')
    simple("/contact/", "Contact", "How to contact Last Day Exam Help.", contact +
           '<p>To report a factual error, see the <a href="/corrections/">corrections policy</a>.</p>')
    ai = ("<p>Some articles and entries are drafted with the help of AI tools. Every item is edited by the editorial team, and calculations, "
          "formulas and answer keys are checked. Items that have not yet had an independent subject review say so on the page.</p>") if AI_DISCLOSURE else ""
    simple("/editorial-standards/", "Editorial Standards", "How Last Day Exam Help writes, checks and updates its content.",
           "<ul><li>Every page has a clear educational purpose and should teach something useful.</li>"
           "<li>Explanations, worked examples and practice questions are original.</li>"
           "<li>Calculations, formulas and answer keys are checked before publication.</li>"
           "<li>Practice questions are never presented as official exam content.</li>"
           "<li>Where curricula differ, we say which qualification or region we mean, or advise checking your own exam board.</li>"
           "<li>Sources are cited only when they are real and support the claim.</li>"
           "<li>Advertising, if used, will be clearly separated from editorial content.</li></ul>" + ai +
           "<h2>Review status</h2><p>Pages show their review status. We only describe a page as independently reviewed once that review has happened.</p>")
    simple("/corrections/", "Corrections Policy", "How errors are reported and corrected.",
           "<p>We want our content to be accurate. If you find a factual error, an incorrect answer or an unclear explanation, tell us using the "
           "details on the <a href=\"/contact/\">contact page</a>, including the page address and what you believe is wrong.</p>"
           "<p>We review reports, correct confirmed errors promptly and, where an error could have misled readers, note the correction on the page. "
           "We do not change publication dates to make old content look new.</p>")
    simple("/privacy/", "Privacy Policy", "How Last Day Exam Help handles visitor information.",
           "<p>Last updated: %s.</p><h2>What we collect</h2>"
           "<p>This site does not require accounts and does not ask you to submit personal information to read content. Search runs in your browser "
           "against a file hosted with the site; your search terms are not sent to a separate search service.</p>"
           "<p>Our hosting provider may keep standard server logs, such as IP address, browser type and the pages requested, for security and "
           "reliability.</p><h2>Cookies and advertising</h2>"
           "<p>The site itself does not set tracking cookies. If we add analytics or advertising in future, we will update this policy, describe the "
           "services used and provide any consent choices required by law.</p><h2>Contact</h2>"
           "<p>Questions about this policy can be sent using the details on the <a href=\"/contact/\">contact page</a>.</p>"
           "<p>This policy describes the site as built. The site owner should review it with a qualified adviser before launch, especially if "
           "advertising or analytics are added.</p>" % PUBLISHED)
    simple("/terms/", "Terms of Use", "Terms of use for Last Day Exam Help.",
           "<p>By using this site you agree to these terms.</p><ul>"
           "<li>Content is provided for general educational purposes. It is not professional, legal, medical or financial advice.</li>"
           "<li>We do not guarantee that content is complete or error-free, or that using it will lead to any particular exam result.</li>"
           "<li>Practice questions are original to this site and are not official exam content.</li>"
           "<li>You may read and share links to our pages. Please do not republish our content in bulk without permission.</li>"
           "<li>We may change or remove content at any time.</li>"
           "<li>To the extent permitted by law, we are not liable for loss arising from use of the site.</li></ul>"
           "<p>The site owner should have these terms reviewed by a qualified adviser before launch.</p>")
    simple("/accessibility/", "Accessibility", "Accessibility information for Last Day Exam Help.",
           "<p>We aim to make the site usable by as many people as possible.</p><ul>"
           "<li>Semantic headings, landmarks and a skip link.</li><li>Keyboard-operable navigation, search and filters with visible focus.</li>"
           "<li>Text colours chosen for strong contrast in light and dark modes.</li>"
           "<li>Layouts that adapt to small screens, and reduced-motion preferences respected.</li>"
           "<li>Answers on practice pages are revealed with native disclosure controls.</li></ul>"
           "<p>We have not yet had a formal accessibility audit. If you find a barrier, please <a href=\"/contact/\">contact us</a>.</p>")


def build_search_and_404():
    page("/search/", "Search", "Search articles, subjects and vocabulary.",
         '<h1>Search</h1><form class="search big" role="search" action="/search/" method="get"><label for="sq">Search the site</label> '
         '<input id="sq" name="q" type="search" autocomplete="off"> <button type="submit">Search</button></form>'
         '<p id="search-status" role="status" aria-live="polite" class="small"></p>'
         '<div id="results"></div><button id="more" type="button" hidden>Show more results</button>'
         '<noscript><p>Search needs JavaScript. You can browse the <a href="/subjects/">subjects</a> and <a href="/vocabulary/">vocabulary</a> instead.</p></noscript>',
         sitemap=False, search=False, noindex=True)
    write("404.html", layout("/404/", "Page not found", "That page does not exist.",
          '<h1>Page not found</h1><p>That page does not exist or has moved. Try the <a href="/subjects/">subjects</a>, '
          '<a href="/vocabulary/">vocabulary</a> or <a href="/blog/">blog</a>, or use the search box above.</p>', noindex=True))


# ------------------------------------------------------------------ assets
CSS = """:root{--bg:#fff;--fg:#1a2233;--muted:#4f5a70;--brand:#1d4ed8;--brand-fg:#fff;--line:#d9dfeb;--soft:#f3f6fc;--warn:#fff3c4;--warn-fg:#4a3b00}
@media(prefers-color-scheme:dark){:root{--bg:#0f1420;--fg:#e8ecf5;--muted:#a9b2c6;--brand:#9bb8ff;--brand-fg:#0b1020;--line:#2a3348;--soft:#171e2e;--warn:#3a3210;--warn-fg:#ffe9a3}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;font:1.0625rem/1.7 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;background:var(--bg);color:var(--fg)}
.wrap{max-width:62rem;margin:0 auto;padding:0 1rem}
a{color:var(--brand)}a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible,summary:focus-visible{outline:3px solid var(--brand);outline-offset:2px}
.skip{position:absolute;left:-999px;top:0}.skip:focus{left:1rem;top:1rem;background:var(--bg);padding:.5rem 1rem;z-index:99;border:2px solid var(--brand)}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.site-header{border-bottom:1px solid var(--line);background:var(--bg)}
.head-row{display:flex;flex-wrap:wrap;gap:.6rem;align-items:center;padding-top:.7rem;padding-bottom:.5rem}
.brand{font-weight:800;font-size:1.25rem;text-decoration:none;color:var(--fg);margin-right:auto}
.search{display:flex;gap:.4rem;flex:1 1 16rem;max-width:28rem}
.search input,.filters input,.filters select{flex:1;padding:.55rem .7rem;border:1px solid var(--line);border-radius:.45rem;background:var(--bg);color:var(--fg);font:inherit}
button,.btn{padding:.55rem 1rem;border:0;border-radius:.45rem;background:var(--brand);color:var(--brand-fg);font:inherit;font-weight:600;text-decoration:none;display:inline-block;cursor:pointer}
.btn.alt{background:var(--soft);color:var(--fg);border:1px solid var(--line)}
.menu-btn{display:none;background:var(--soft);color:var(--fg);border:1px solid var(--line)}
.nav{list-style:none;margin:0;padding:.2rem 0 .7rem;display:flex;flex-wrap:wrap;gap:.2rem 1.1rem}
.nav a{text-decoration:none;color:var(--fg);padding:.25rem 0;display:inline-block}.nav a[aria-current]{font-weight:700;border-bottom:2px solid var(--brand)}
@media(max-width:46rem){.js .menu-btn{display:inline-block}.js .nav{display:none;flex-direction:column;padding-bottom:.9rem}.js .nav.open{display:flex}.nav a{padding:.5rem 0}.search{order:3;flex-basis:100%;max-width:none}}
main{padding-top:1.2rem;padding-bottom:3rem}h1{line-height:1.2;font-size:2rem}h2{margin-top:2rem;line-height:1.3}h3{line-height:1.3}
.lead{font-size:1.2rem;color:var(--muted)}.hero{padding:1.5rem 0 .5rem}.hero h1{font-size:2.4rem}
.cards{list-style:none;padding:0;display:grid;gap:.75rem;grid-template-columns:repeat(auto-fill,minmax(16rem,1fr))}
.cards li{border:1px solid var(--line);border-radius:.6rem;padding:.85rem 1rem;background:var(--soft);display:flex;flex-direction:column;gap:.25rem}
.cards span{color:var(--muted);font-size:.95rem}.tag{font-style:normal;font-size:.8rem;color:var(--muted)}
.crumbs ol{list-style:none;display:flex;flex-wrap:wrap;gap:.4rem;padding:0;margin:0 0 1rem;font-size:.9rem}.crumbs li+li::before{content:"/";margin-right:.4rem;color:var(--muted)}
.meta,.small{color:var(--muted);font-size:.92rem}.az a{display:inline-block;padding:.15rem .45rem;font-weight:700}
.filters{display:flex;flex-wrap:wrap;gap:.6rem;align-items:center;margin:1rem 0}.filters label{font-weight:600}
.toc{border:1px solid var(--line);border-radius:.6rem;padding:.8rem 1rem;background:var(--soft);margin:1rem 0}.toc ul{margin:.3rem 0 0;padding-left:1.2rem}
.table-wrap{overflow-x:auto}table{border-collapse:collapse;margin:1rem 0;min-width:20rem}th,td{border:1px solid var(--line);padding:.5rem .7rem;text-align:left;vertical-align:top}th{background:var(--soft)}
pre{background:var(--soft);border:1px solid var(--line);border-radius:.5rem;padding:.8rem 1rem;overflow-x:auto;line-height:1.5}code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.95em}
.q{border:1px solid var(--line);border-radius:.6rem;padding:.5rem 1rem 1rem;margin:1rem 0}.opts{list-style:none;padding:0}.opts li{padding:.2rem 0}
details summary{cursor:pointer;font-weight:600;color:var(--brand)}
.about-box,.notice{border:1px solid var(--line);background:var(--soft);border-radius:.6rem;padding:.8rem 1rem;margin:2rem 0;font-size:.92rem;color:var(--muted)}
.site-footer{border-top:1px solid var(--line);padding:1.5rem 0;color:var(--muted);background:var(--soft)}
.big{max-width:none;margin:1rem 0}[hidden]{display:none!important}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
@media print{.site-header,.site-footer,.search,.skip{display:none}body{font-size:12pt}}
"""

JS = r"""(function(){
var btn=document.querySelector('.menu-btn'),nav=document.getElementById('nav-list');
if(btn&&nav){btn.addEventListener('click',function(){var o=nav.classList.toggle('open');btn.setAttribute('aria-expanded',o?'true':'false');});}

/* vocabulary filter */
var vq=document.querySelector('[data-vocab-q]'),vs=document.querySelector('[data-vocab-s]');
if(vq&&vs){
  var items=[].slice.call(document.querySelectorAll('li[data-subject]'));
  var secs=[].slice.call(document.querySelectorAll('[data-letter]'));
  var st=document.getElementById('vocab-status'),empty=document.getElementById('vocab-empty');
  var run=function(){
    var q=vq.value.trim().toLowerCase(),s=vs.value,n=0;
    items.forEach(function(li){
      var ok=(!s||li.dataset.subject===s)&&(!q||li.dataset.text.indexOf(q)>-1);
      li.hidden=!ok;if(ok)n++;
    });
    secs.forEach(function(sec){sec.hidden=!sec.querySelector('li:not([hidden])');});
    st.textContent=(q||s)?n+' term'+(n===1?'':'s')+' shown':'';
    empty.hidden=n>0;
  };
  vq.addEventListener('input',run);vs.addEventListener('change',run);
  var p=new URLSearchParams(location.search).get('q');if(p){vq.value=p;run();}
}

/* site search */
var box=document.getElementById('results');
if(box){
  var more=document.getElementById('more'),status=document.getElementById('search-status');
  var sq=document.getElementById('sq'),hdr=document.getElementById('q');
  var q=(new URLSearchParams(location.search).get('q')||'').trim();
  if(sq)sq.value=q;if(hdr)hdr.value=q;
  var hits=[],shown=0,PAGE=20;
  var render=function(){
    var ul=box.querySelector('ul');
    if(!ul){ul=document.createElement('ul');ul.className='cards';box.appendChild(ul);}
    hits.slice(shown,shown+PAGE).forEach(function(h){
      var li=document.createElement('li'),a=document.createElement('a'),b=document.createElement('strong'),s=document.createElement('span'),t=document.createElement('em');
      a.href=h.u;b.textContent=h.t;a.appendChild(b);s.textContent=h.d;t.className='tag';t.textContent=h.k;
      li.appendChild(a);li.appendChild(s);li.appendChild(t);ul.appendChild(li);
    });
    shown=Math.min(hits.length,shown+PAGE);more.hidden=shown>=hits.length;
  };
  if(!q){status.textContent='Type a word or phrase above to search.';}
  else{
    status.textContent='Searching…';
    fetch('/assets/search-index.json').then(function(r){if(!r.ok)throw 0;return r.json();}).then(function(idx){
      var w=q.toLowerCase().split(/\s+/).filter(Boolean);
      idx.forEach(function(i){
        var t=i.t.toLowerCase(),h=(i.h||'').toLowerCase(),d=i.d.toLowerCase(),score=0,ok=true;
        w.forEach(function(x){
          var sc=0;
          if(t===x)sc=100;else if(t.indexOf(x)===0)sc=60;else if(t.indexOf(x)>-1)sc=40;
          else if(h.indexOf(x)>-1)sc=15;else if(d.indexOf(x)>-1)sc=8;
          if(!sc)ok=false;score+=sc;
        });
        if(ok){i.s=score;hits.push(i);}
      });
      hits.sort(function(a,b){return b.s-a.s||a.t.localeCompare(b.t);});
      if(!hits.length){status.textContent='No results for “'+q+'”. Try a shorter or different word, or browse the subjects and vocabulary.';return;}
      status.textContent=hits.length+' result'+(hits.length===1?'':'s')+' for “'+q+'”';
      render();more.addEventListener('click',render);
    }).catch(function(){status.textContent='Search is unavailable right now. Please browse the subjects or vocabulary instead.';});
  }
}
})();
"""

FAVICON = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#1d4ed8"/>'
           '<path d="M16 44V20h6v18h12v6zM38 20h6v24h-6z" fill="#fff"/></svg>')


def build_assets():
    write("assets/style.css", CSS)
    write("assets/site.js", JS)
    write("assets/favicon.svg", FAVICON)
    write("assets/search-index.json", json.dumps(SEARCH, separators=(",", ":")))


def build_feeds():
    urls = "".join("<url><loc>%s%s</loc><lastmod>%s</lastmod></url>" % (SITE, u, PUBLISHED) for u in PAGES)
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>' % urls)
    if NOINDEX:
        robots = "User-agent: *\nDisallow: /\n"
    else:
        robots = "User-agent: *\nAllow: /\nDisallow: /search/\n"
    write("robots.txt", robots + "\nSitemap: %s/sitemap.xml\n" % SITE)
    d = datetime.datetime.strptime(PUBLISHED, "%Y-%m-%d").strftime("%a, %d %b %Y 00:00:00 GMT")
    items = "".join("<item><title>%s</title><link>%s/blog/%s/</link><guid>%s/blog/%s/</guid><pubDate>%s</pubDate><description>%s</description></item>"
                    % (e(a["title"]), SITE, a["slug"], SITE, a["slug"], d, e(a["description"])) for a in ARTICLES)
    write("rss.xml", '<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>%s</title><link>%s/</link><description>%s</description>%s</channel></rss>'
          % (BRAND, SITE, e(TAGLINE), items))


# ------------------------------------------------------------------ verify output
def verify():
    pages = glob.glob(OUT + "/**/*.html", recursive=True)
    checked = 0
    for f in pages:
        s = open(f, encoding="utf-8").read()
        ids = set(re.findall(r'\bid="([^"]+)"', s))
        for h in re.findall(r'(?:href|src)="([^"]+)"', s):
            if h.startswith(("http", "mailto:", "data:")):
                continue
            path, _, frag = h.partition("#")
            path = path.split("?")[0]
            checked += 1
            if not path:
                if frag and frag not in ids:
                    err("%s: missing anchor #%s" % (f, frag))
                continue
            t = os.path.join(OUT, path.lstrip("/"))
            if path.endswith("/"):
                t = os.path.join(t, "index.html")
            if not os.path.exists(t):
                err("%s: broken link %s" % (f, h))
    return len(pages), checked


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    build_vocab()
    psubs = build_practice()
    build_articles(psubs)
    build_hubs()
    build_home(psubs)
    build_trust()
    build_search_and_404()
    build_assets()
    build_feeds()
    npages, nlinks = verify()
    print("Articles: %d | glossary terms: %d | practice questions: %d" % (len(ARTICLES), len(TERMS), len(PRACTICE)))
    print("HTML pages: %d | internal links checked: %d | sitemap URLs: %d" % (npages, nlinks, len(PAGES)))
    print("Indexing: %s" % ("BLOCKED (set CONTACT_EMAIL to enable)" if NOINDEX else "allowed"))
    if ERRORS:
        print("\n%d PROBLEM(S):" % len(ERRORS))
        for x in ERRORS[:60]:
            print(" -", x)
        sys.exit(1)
    print("No content or link problems found.")


if __name__ == "__main__":
    main()
