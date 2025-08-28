import json
from collections import defaultdict

# Mapping verdicts to LaTeX macros
verdict_map = {
    "Medium": r"\partialCompliant",
    "High": r"\fullCompliant",
    "Low": r"\notCompliant"
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
sources = ["arbitrator", "manual"]

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
    "hybrid": "Hybrid",
    "unknown": "Unknown"
}

row_count_per_category = {cat: 0 for cat in category_mapping.keys()}
# Count rows per category
for category, papers in grouped_by_category.items():
    row_count_per_category[category] = len(papers)

# Desired category order
category_order = ["feature-based", "similarity-based", "identity-based", "hybrid", "unknown"]

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
        row = f"{cat_value} & {name}~\\cite{{{key}}}"
        
        for metric in metrics:
            metric_block = content.get(metric, {})
            llm_verdict = metric_block.get("arbitrator", "")
            manual_verdict = metric_block.get("manual", "")

            if isinstance(llm_verdict, dict):
                llm_verdict = llm_verdict.get("value", "")
            if isinstance(manual_verdict, dict):
                manual_verdict = manual_verdict.get("value", "")

            for src, verdict_value in zip(sources, [llm_verdict, manual_verdict]):
                verdict_symbol = verdict_map.get(verdict_value, "")
                if llm_verdict != manual_verdict:
                    verdict_symbol = f"\\cellcolor{{gray!20}} {verdict_symbol}"
                row += f" & {verdict_symbol}"
        
        row += r"\\ \hline \hline" if i == row_count_per_category[category] - 1 else r" \\ \cline{2-16}"
        latex_rows.append(row)

# Output LaTeX rows
for row in latex_rows:
    print(row)
