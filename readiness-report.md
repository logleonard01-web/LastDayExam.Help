# Last Day Exam Help: AdSense and Launch Readiness Report

Generated alongside the build. This report improves readiness. It does not predict or guarantee AdSense approval, rankings or exam results. Google makes the final approval decision. "Passed" is used only where the build or a check produced evidence.

## Status key

Passed | Failed | Needs manual verification | Not applicable

## Checklist

| # | Requirement | Status | Evidence | Required action | Priority |
|---|---|---|---|---|---|
| 1 | Useful original educational content exists | Passed | 44 articles, 119 glossary entries, 47 practice questions written for this site | None for existence; see items 2 and 3 | High |
| 2 | Guides reach the 800-1,500 word target for substantial guides | Failed | Average article is about 330 words; longest cornerstone guide is about 690 | Expand the cornerstone guides first, then the supporting guides; add sources | High |
| 3 | Independent subject review completed | Failed | No independent review has happened; every page says "awaiting independent review" | Have a qualified person review maths, science and facts before launch | High |
| 4 | Calculations, formulas and answer keys checked | Passed | Worked examples and all 47 answer keys were hand-checked; the build verifies each multiple-choice answer is one of its options | Re-check after any edit | High |
| 5 | Sources cited and real | Needs manual verification | No external citations added yet, so none can be false; some claims (for example sleep guidance) would benefit from named sources | Add real, verified sources to claim-dependent articles | Medium |
| 6 | About page | Passed | /about/ exists with mission and limits | Add the real publisher name and background supplied by the owner | High |
| 7 | Contact page with a working contact method | Failed | /contact/ shows a notice because `CONTACT_EMAIL` is not set | Set `CONTACT_EMAIL`, rebuild | High |
| 8 | Privacy policy | Needs manual verification | /privacy/ is written to match the site as built (no accounts, no cookies) | Have it reviewed; update before adding analytics or ads | High |
| 9 | Terms of use | Needs manual verification | /terms/ exists, generic | Have it reviewed | Medium |
| 10 | Editorial standards and corrections policy | Passed | /editorial-standards/ and /corrections/ exist and describe the real process, including AI-assisted drafting | Keep in sync with practice | Medium |
| 11 | Navigation links work | Passed | Build checked 6,967 internal links and anchors across 195 pages; zero broken | Re-run build after each change | High |
| 12 | Essential pages exist | Passed | Home, subjects, hubs, blog, glossary, practice, trust pages, search, 404, sitemap, robots, RSS | None | High |
| 13 | No empty archives or doorway pages | Passed | Every hub lists real content; no keyword-variant pages | Keep it that way when expanding | Medium |
| 14 | HTTPS works | Needs manual verification | Handled by hosting after deploy | Check https://lastdayexam.help/ after deployment | High |
| 15 | No redirect loops; correct status codes | Needs manual verification | `vercel.json` defines www to apex redirect and a few aliases | Test live URLs and the 404 page | High |
| 16 | Sitemap valid | Needs manual verification | Well-formed XML with 193 URLs generated | Submit in Search Console and check for errors | Medium |
| 17 | robots.txt appropriate | Failed (intentional for now) | Currently `Disallow: /` while `CONTACT_EMAIL` is unset | Set `CONTACT_EMAIL`; rebuild to allow crawling | High |
| 18 | Structured data accurate | Needs manual verification | Article and BreadcrumbList JSON-LD on pages; no fake ratings, reviews or people | Validate with Google's Rich Results Test | Medium |
| 19 | Mobile usability | Needs manual verification | Mobile-first CSS and a collapsing menu are in place; not tested on devices | Test on real phones and Lighthouse | High |
| 20 | Page performance | Needs manual verification | No frameworks, one small CSS and one small JS file; not measured | Run PageSpeed Insights after deploy | Medium |
| 21 | Accessibility | Needs manual verification | Semantic headings, skip link, focus styles, labelled forms, reduced-motion support; no formal audit | Run an audit and keyboard-test | Medium |
| 22 | Ads clearly distinguished, no accidental-click layouts | Not applicable | No ads implemented | Apply when ads are added, following current AdSense instructions | Low |
| 23 | ads.txt | Not applicable | No publisher ID yet | Add after AdSense approval | Low |
| 24 | Consent and privacy for ads and analytics | Not applicable | None used yet | Add a compliant consent setup before ads | Low |

## Content status

| Status | Count |
|---|---|
| Published (awaiting independent review) | 44 |
| Planned | 456 |

See `roadmap.csv` for the full 500-idea editorial database.

## Before launch, in order

1. Set the real contact email and publisher details; rebuild.
2. Get an independent review of the content and record the reviewer only if they agree.
3. Expand the cornerstone guides and add verified sources.
4. Deploy, then test HTTPS, redirects, 404, mobile and speed.
5. Submit the sitemap in Search Console.
6. Only then consider an AdSense application.
