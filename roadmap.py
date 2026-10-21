#!/usr/bin/env python3
"""Builds roadmap.csv: the 500-idea editorial database for Last Day Exam Help.

Rows 1..N are the articles actually published by build.py (read from content/*.md).
Remaining rows are planned ideas, deduplicated by slug, balanced across clusters.
Statuses are truthful: nothing is 'Approved' or 'Reviewed' because no independent review has happened.
"""
import csv
import glob
import re

TARGET = 500

CLUSTERS = {
    "Exam preparation": dict(
        hub="/exam-preparation/", reader="Students in the last days before an exam", style="direct",
        extras=[],
        research="Check advice against exam-board guidance; avoid extreme schedules; keep wellbeing advice general and non-medical.",
        topics=["Planning the final day before an examination", "Creating a realistic last-day revision schedule",
                "Choosing which topics to review first", "Reviewing several subjects in limited time", "Identifying knowledge gaps",
                "Reviewing difficult concepts", "Creating concise revision notes", "Using practice questions effectively",
                "Reviewing mistakes from previous tests", "Understanding examination instructions", "Preparing for multiple-choice tests",
                "Preparing for essay examinations", "Preparing for short-answer examinations", "Revising mathematics formulas",
                "Revising scientific definitions", "Reviewing historical timelines", "Reviewing vocabulary before an exam",
                "Using a final revision checklist", "Organizing books and examination materials", "Understanding question command words",
                "Allocating time during a test", "Checking answers before submission", "Approaching unfamiliar questions",
                "Distinguishing essential concepts from supporting details", "Avoiding inefficient revision habits",
                "Planning breaks and protecting sleep", "Managing ordinary examination stress", "Building a realistic exam-day routine"]),
    "Mathematics": dict(
        hub="/subjects/mathematics/", reader="Students revising mathematics", style="explained",
        extras=["Worked examples", "Common mistakes", "Quick revision"],
        research="Verify every formula and calculation; state notation conventions; check against a standard curriculum reference.",
        topics=["Number sense", "Whole numbers", "Integers", "Negative numbers", "Fractions", "Decimals", "Percentages", "Ratios",
                "Proportions", "Factors and multiples", "Prime numbers", "Exponents", "Roots", "Scientific notation", "Unit conversion",
                "Variables", "Algebraic expressions", "Equations", "Inequalities", "Linear equations", "Simultaneous equations",
                "Polynomials", "Factoring", "Quadratic equations", "Functions", "Graphs of functions", "Sequences", "Exponential expressions",
                "Logarithms", "Algebra word problems", "Points, lines and planes", "Angles", "Triangles", "Quadrilaterals", "Polygons",
                "Circles", "Area", "Perimeter", "Volume", "Surface area", "Coordinate geometry", "Transformations", "Similarity",
                "Congruence", "Geometric proofs", "Trigonometry", "Probability", "Statistics", "Probability distributions",
                "Combinatorics", "Limits", "Derivatives", "Integrals", "Differential equations", "Vectors", "Matrices", "Mathematical logic"]),
    "Biology": dict(
        hub="/subjects/science/", reader="Students revising biology", style="explained",
        extras=["Quick revision", "Common mistakes", "Worked examples"],
        research="Check against a standard biology reference; specify the level (secondary, introductory college) and any exam-board differences.",
        topics=["Cells and organelles", "Cell division", "Genetics", "DNA and RNA", "Evolution", "Natural selection", "Ecosystems",
                "Food webs", "Photosynthesis", "Cellular respiration", "Human body systems", "Homeostasis", "Microorganisms",
                "Classification of living things", "Designing biology experiments"]),
    "Chemistry": dict(
        hub="/subjects/science/", reader="Students revising chemistry", style="explained",
        extras=["Worked examples", "Common mistakes", "Quick revision"],
        research="Verify formulas, equations and calculations; use SI units; state safety guidance only in general terms and defer to the teacher.",
        topics=["Atoms", "Elements", "Compounds", "Mixtures", "The periodic table", "Chemical bonding", "Chemical equations",
                "Balancing equations", "Acids and bases", "pH", "Chemical reactions", "Mole calculations", "Solutions",
                "States of matter", "Organic chemistry fundamentals", "Laboratory safety"]),
    "Physics": dict(
        hub="/subjects/science/", reader="Students revising physics", style="explained",
        extras=["Worked examples", "Common mistakes", "Quick revision"],
        research="Verify equations, units and numerical answers; state values of constants used.",
        topics=["Motion", "Velocity", "Acceleration", "Forces", "Newton's laws", "Work and energy", "Momentum", "Gravity", "Waves",
                "Sound", "Light", "Electricity", "Magnetism", "Electric circuits", "Thermodynamics", "Pressure", "Units and measurement"]),
    "Earth and environmental science": dict(
        hub="/subjects/science/", reader="Students revising earth and environmental science", style="explained",
        extras=["Quick revision", "Common mistakes"],
        research="Use current data only from named official sources (for example national science agencies) and record the date accessed.",
        topics=["Earth science", "Astronomy", "Environmental science", "Climate science", "Scientific methodology",
                "Data interpretation in science", "Experimental variables", "Graphs and scientific measurements"]),
    "English and literature": dict(
        hub="/subjects/english/", reader="Students revising English", style="explained",
        extras=["Common mistakes", "Worked examples", "Quick revision"],
        research="Use original examples; do not reproduce copyrighted passages; define terms consistently with a standard grammar reference.",
        topics=["Parts of speech", "Nouns and pronouns", "Verbs and tenses", "Adjectives and adverbs", "Prepositions", "Conjunctions",
                "Subject-verb agreement", "Sentence structure", "Clauses and phrases", "Punctuation", "Spelling",
                "Commonly confused words", "Reading comprehension", "Inference", "Main ideas", "Supporting evidence", "Essay structure",
                "Thesis statements", "Argumentative writing", "Persuasive techniques", "Literary analysis", "Poetry",
                "Metaphors and similes", "Personification", "Irony", "Symbolism", "Tone and mood", "Theme and characterization",
                "Narrative perspective", "Rhetorical devices", "Academic writing", "Vocabulary development"]),
    "History and geography": dict(
        hub="/subjects/history/", reader="Students revising history and geography", style="explained",
        extras=["Quick revision", "Common mistakes"],
        research="State the geographic and curricular scope; verify dates and facts against reputable references; distinguish fact from interpretation.",
        topics=["Ancient civilizations", "World history overview", "U.S. history overview", "Major historical periods", "Historical timelines",
                "Primary sources", "Secondary sources", "Historical causation", "Historical interpretation", "Geography fundamentals",
                "Maps and coordinates", "Latitude and longitude", "Climate", "Weather", "Landforms", "Population", "Migration",
                "Urbanization", "Natural resources", "Government", "Civics", "Economics in history and geography",
                "Political and social terminology"]),
    "Computer science": dict(
        hub="/subjects/computer-science/", reader="Students revising computing", style="explained",
        extras=["Worked examples", "Common mistakes", "Quick revision"],
        research="Test every code example by running it; state the language and version.",
        topics=["Computer fundamentals", "Hardware and software", "Operating systems", "Programming concepts", "Variables and data types",
                "Conditions and loops", "Functions", "Algorithms", "Data structures", "Databases", "Networks", "Internet terminology",
                "Cybersecurity fundamentals", "Digital literacy", "Artificial intelligence literacy", "Computing mathematics",
                "Information systems", "Responsible technology use"]),
    "Economics and financial literacy": dict(
        hub="/subjects/economics/", reader="Students revising economics and business", style="explained",
        extras=["Worked examples", "Common mistakes", "Quick revision"],
        research="Use official statistical sources for any data and record the date; present general information, never personal financial advice.",
        topics=["Supply and demand", "Scarcity", "Opportunity cost", "Markets", "Competition", "Inflation", "Interest", "Economic growth",
                "Productivity", "Employment", "Entrepreneurship", "Accounting fundamentals", "Revenue and expenses", "Profit and loss",
                "Budgeting", "Financial literacy", "Business vocabulary", "Economic indicators", "Basic financial calculations"]),
    "Research and academic writing": dict(
        hub="/subjects/research-writing/", reader="Students writing research and essays", style="explained",
        extras=["Common mistakes", "Quick revision", "Worked examples"],
        research="Describe citation styles from their official guides; do not mix styles; give original examples.",
        topics=["Research questions", "Thesis statements in research", "Outlining", "Source evaluation", "Evidence", "Citations",
                "Referencing styles", "Paraphrasing", "Summarizing", "Academic tone", "Research methods", "Research variables",
                "Data collection", "Tables and figures", "Editing", "Proofreading", "Plagiarism prevention", "Argument structure",
                "Evaluating claims"]),
    "Languages and linguistics": dict(
        hub="/subjects/english/", reader="Students of language and linguistics", style="explained",
        extras=["Quick revision", "Common mistakes"],
        research="Verify etymologies and phonetic details in a reputable dictionary or linguistics reference; never guess origins.",
        topics=["Grammar", "Syntax", "Semantics", "Phonetics", "Phonology", "Etymology", "Word formation", "Prefixes", "Suffixes",
                "Word roots", "Idioms", "Figurative language", "Language acquisition", "Vocabulary-learning techniques",
                "Translation concepts", "Multilingual learning"]),
    "Critical thinking": dict(
        hub="/subjects/critical-thinking/", reader="Students and independent learners", style="explained",
        extras=["Common mistakes", "Worked examples", "Quick revision"],
        research="Use original examples; cite research on cognitive claims only from real, verifiable studies.",
        topics=["Logical reasoning", "Deductive reasoning", "Inductive reasoning", "Evidence evaluation", "Logical fallacies", "Assumptions",
                "Correlation and causation", "Scientific reasoning", "Media literacy", "Information literacy", "Research credibility",
                "Argument analysis", "Problem-solving", "Ethical reasoning", "Interpreting charts and data"]),
}

# Topics already covered by a published article (explainer skipped; extras still allowed)
COVERED = {
    "planning the final day before an examination", "creating a realistic last-day revision schedule", "creating concise revision notes",
    "using practice questions effectively", "preparing for multiple-choice tests", "preparing for essay examinations",
    "using a final revision checklist", "understanding question command words", "allocating time during a test",
    "checking answers before submission", "planning breaks and protecting sleep", "managing ordinary examination stress",
    "fractions", "percentages", "linear equations", "quadratic equations", "area", "perimeter", "volume", "probability",
    "photosynthesis", "newton's laws", "balancing equations", "acids and bases", "ph", "cells and organelles",
    "velocity", "acceleration", "essay structure", "thesis statements", "commonly confused words", "metaphors and similes",
    "primary sources", "secondary sources", "latitude and longitude", "historical causation", "algorithms", "variables and data types",
    "conditions and loops", "supply and demand", "opportunity cost", "inflation", "citations", "source evaluation", "paraphrasing",
    "correlation and causation", "logical fallacies", "scientific methodology", "experimental variables",
}


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def title_for(topic, kind, style):
    if kind == "Explainer":
        return topic if style == "direct" else "%s Explained" % topic
    if kind == "Worked examples":
        return "%s: Worked Examples with Solutions" % topic
    if kind == "Common mistakes":
        return "Common Mistakes with %s and How to Fix Them" % topic
    return "%s: Quick Revision Guide" % topic


OBJECTIVE = {
    "Explainer": "Understand %s well enough to explain it in your own words and apply it in an exam question.",
    "Worked examples": "Follow fully worked, original examples of %s and reproduce the method on a new problem.",
    "Common mistakes": "Recognise the typical errors made with %s and apply a checking habit to avoid them.",
    "Quick revision": "Review the essential ideas, vocabulary and a worked example for %s in one short sitting.",
}
INTENT = {"Explainer": "Informational: what is it and how does it work",
          "Worked examples": "Informational: how do I solve this type of problem",
          "Common mistakes": "Informational: why am I losing marks and how do I stop",
          "Quick revision": "Informational: summary to revise from shortly before an exam"}
GROUP = {"Explainer": "Supporting explainer", "Worked examples": "Worked example", "Common mistakes": "Supporting explainer",
         "Quick revision": "Quick revision"}
QUESTIONS = {"Explainer": "What is it? Why does it matter? What are the key terms and a simple example?",
             "Worked examples": "How do I carry out the method step by step? How do I check my answer?",
             "Common mistakes": "Which errors are most common? How can I spot and correct them?",
             "Quick revision": "What must I remember? What is one worked example? What are the pitfalls?"}


def read_published():
    rows = []
    for f in sorted(glob.glob("content/*.md")):
        raw = open(f, encoding="utf-8").read()
        for chunk in re.split(r"(?m)^=== ", raw)[1:]:
            slug, rest = chunk.split("\n", 1)
            head, body = rest.split("\n---\n", 1)
            meta = {}
            for ln in head.strip().split("\n"):
                k, v = ln.split(":", 1)
                meta[k.strip()] = v.strip()
            meta["slug"] = slug.strip()
            meta["words"] = len(re.findall(r"\w+", body))
            rows.append(meta)
    return rows


SUBJECT_TO_CLUSTER = {
    "exam-prep": "Exam preparation", "study-skills": "Exam preparation", "mathematics": "Mathematics", "science": "Biology",
    "english": "English and literature", "history": "History and geography", "computer-science": "Computer science",
    "economics": "Economics and financial literacy", "research-writing": "Research and academic writing", "critical-thinking": "Critical thinking",
}


def main():
    published = read_published()
    seen = set()
    rows = []
    for p in published:
        cl = SUBJECT_TO_CLUSTER.get(p["subject"], "Exam preparation")
        cfg = CLUSTERS[cl]
        seen.add(p["slug"])
        rows.append(dict(
            Title=p["title"], Slug=p["slug"], Category=cl, Cluster=cl, Group=p["kind"],
            Reader=cfg["reader"], SearchIntent="Informational", Objective=p["description"],
            Questions="See article", Vocabulary=p.get("vocab", ""), Examples="Included in article",
            PracticeOpps="Practice questions at /practice/%s/" % p.get("practice", ""), Research="Claims and calculations checked by the editorial team; no external sources cited yet.",
            Links=cfg["hub"] + ", " + p.get("related", ""), Status="Published", Review="Awaiting independent review",
            Update="Add sources where claims depend on them; consider expanding toward 800 words" if p["words"] < 700 else "Routine review",
            Words=p["words"]))

    candidates = []
    for cl, cfg in CLUSTERS.items():
        for t in cfg["topics"]:
            if t.lower() not in COVERED:
                candidates.append((0, cl, t, "Explainer"))
    # extras: round-robin by cluster for balance
    extra_by_cluster = {}
    for cl, cfg in CLUSTERS.items():
        lst = []
        for k in range(3):
            for t in cfg["topics"]:
                if k < len(cfg["extras"]):
                    lst.append((cl, t, cfg["extras"][k]))
        extra_by_cluster[cl] = lst
    idx = 0
    while any(extra_by_cluster.values()):
        for cl in CLUSTERS:
            if extra_by_cluster[cl]:
                c, t, k = extra_by_cluster[cl].pop(0)
                candidates.append((1, c, t, k))
    candidates.sort(key=lambda x: x[0])  # stable: explainers first, then round-robin extras

    for _, cl, topic, kind in candidates:
        if len(rows) >= TARGET:
            break
        cfg = CLUSTERS[cl]
        title = title_for(topic, kind, cfg["style"])
        slug = slugify(title)
        if slug in seen:
            continue
        seen.add(slug)
        rows.append(dict(
            Title=title, Slug=slug, Category=cl, Cluster=topic, Group=GROUP[kind], Reader=cfg["reader"],
            SearchIntent=INTENT[kind], Objective=OBJECTIVE[kind] % topic.lower(), Questions=QUESTIONS[kind],
            Vocabulary="To be defined from glossary", Examples="Two to three original examples",
            PracticeOpps="3 to 5 original questions with checked answers", Research=cfg["research"],
            Links=cfg["hub"] + ", /vocabulary/, /practice/", Status="Planned", Review="Not started",
            Update="Review after publication; update if curricula change", Words=""))

    assert len(rows) == TARGET, len(rows)
    assert len({r["Slug"] for r in rows}) == TARGET
    fields = ["Title", "Slug", "Category", "Cluster", "Group", "Reader", "SearchIntent", "Objective", "Questions", "Vocabulary",
              "Examples", "PracticeOpps", "Research", "Links", "Status", "Review", "Update", "Words"]
    names = {"Title": "Title", "Slug": "Slug", "Category": "Category", "Cluster": "Topic cluster", "Group": "Content group",
             "Reader": "Intended reader", "SearchIntent": "Search intent", "Objective": "Core learning objective",
             "Questions": "Questions answered", "Vocabulary": "Supporting vocabulary", "Examples": "Suggested examples",
             "PracticeOpps": "Practice question opportunities", "Research": "Research requirements", "Links": "Internal link targets",
             "Status": "Publication status", "Review": "Editorial review status", "Update": "Update requirements", "Words": "Word count (published)"}
    with open("roadmap.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([names[k] for k in fields])
        for r in rows:
            w.writerow([r[k] for k in fields])
    from collections import Counter
    print("rows:", len(rows), "| published:", sum(1 for r in rows if r["Status"] == "Published"), "| planned:", sum(1 for r in rows if r["Status"] == "Planned"))
    for k, v in Counter(r["Category"] if r["Status"] == "Published" else r["Category"] for r in rows).most_common():
        print("  %-36s %d" % (k, v))


if __name__ == "__main__":
    main()
