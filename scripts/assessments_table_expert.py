import json
from collections import defaultdict

# Mapping verdicts to LaTeX macros
verdict_map = {
    "Medium": r"\partialCompliant",
    "High": r"\fullCompliant",
    "Low": r"\notCompliant"
}

# Optional normalization in case your JSON uses variants
normalize_verdict = {
    "high": "High",
    "full": "High",
    "fully compliant": "High",

    "medium": "Medium",
    "partial": "Medium",
    "partially compliant": "Medium",

    "low": "Low",
    "none": "Low",
    "non compliant": "Low",
    "non-compliant": "Low",
}

# Metric and model source order
metrics = [
    "f1-coverage",
    "f2-benign-diversity",
    "f3-interpretability",
    "f4-evaluation-thoroughness",
    "s1-concept-drift",
    "s2-active-attack",
    "s3-privacy",
]
sources = ["manual"]

# Load JSON data
with open("assessments_new/assessments.json", "r") as f:
    data = json.load(f)

# Group papers by category
grouped_by_category = defaultdict(list)
for paper, content in data.items():
    category = content.get("category", "unknown")
    grouped_by_category[category].append((paper, content))

category_mapping = {
    "feature-based": "Feature",
    "similarity-based": "Similarity",
    "identity-based": "Identity",
    "hybrid": "Hybrid"
}

row_count_per_category = {cat: 0 for cat in category_mapping.keys()}
# Count rows per category
for category, papers in grouped_by_category.items():
    row_count_per_category[category] = len(papers)

# Desired category order
category_order = ["feature-based", "similarity-based", "identity-based", "hybrid"]

latex_rows = []

# Generate LaTeX rows
for category in category_order:
    rows = grouped_by_category.get(category, [])
    # Sort rows by year (desc), citation_count (desc)
    rows.sort(key=lambda x: (
        -int(x[1].get("year", "0") or 0),
        -int(x[1].get("citation_count", "0") or 0)
    ))

    for i, (paper, content) in enumerate(rows):

        cat_value = f"\\multirow{{{row_count_per_category[category]}}}{{*}}{{\\rotatebox{{90}}{{\\textbf{{{category_mapping[category]}}}}}}}" if i == 0 else ""

        name = content.get("name", "Unknown")
        key = content.get("key", "missingkey")
        year = content.get("year", "unknown")
        row = f"{cat_value} & {name}~\\cite{{{key}}} & {year}"

        # NEW: counters for High/Medium/Low per paper
        count_high = 0
        count_med = 0
        count_low = 0

        for metric in metrics:
            metric_block = content.get(metric, {})
            entry = ""
            for src in sources:
                e = metric_block.get(src, "")
                if isinstance(e, dict):
                    e = e.get("verdict", "")
                if e:  # prefer the first non-empty source entry
                    entry = e
                    break

            # normalize verdict label
            if isinstance(entry, str):
                norm = normalize_verdict.get(entry.strip().lower(), None)
                label = norm if norm in verdict_map else (entry if entry in verdict_map else "")
            else:
                label = ""

            # Count and write the LaTeX macro cell
            if label == "High":
                count_high += 1
            elif label == "Medium":
                count_med += 1
            elif label == "Low":
                count_low += 1

            macro = verdict_map.get(label, "")
            row += f" & {macro}"

        if count_high>1:
            count_high = f"\\cellcolor{{gray!20}} {count_high}"
        # Append the summary column as "#High / #Med / #Low"
        row += f" & {count_high}/{count_med}/{count_low}"

        # NOTE: column count changed (added summary col). Update clines to 11.
        row += r"\\ \hline \hline " if i == row_count_per_category[category]-1 else r" \\ \hhline{~*{10}{-}}"
        latex_rows.append(row)

for row in latex_rows:
    print(row)
