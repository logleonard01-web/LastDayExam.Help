# Last Day Exam Help

Educational site at https://lastdayexam.help/ : study guides, an academic vocabulary library, quick-revision guides and original practice questions.

## How it works

- `content/*.md` holds the articles, `content/glossary.txt` the vocabulary, `content/practice.txt` the practice questions.
- `python3 build.py` generates the static site into `site/` (no dependencies) and checks internal links and content references. It exits with an error if anything is broken.
- `vercel.json` runs that build and serves `site/`.
- `roadmap.csv` is the 500-idea editorial database (`python3 roadmap.py` regenerates it).
- `readiness-report.md` lists launch and AdSense readiness items with honest statuses.

## Before launch

The site is set to `noindex` and `robots.txt` blocks crawlers until a real contact email is set:

```
CONTACT_EMAIL=you@example.com python3 build.py
```

On Vercel, set `CONTACT_EMAIL` as an environment variable instead.
