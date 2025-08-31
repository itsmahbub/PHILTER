import json
from collections import defaultdict, Counter

# Metrics and their LaTeX column order
metric_keys = [
    "f1-coverage",
    "f2-benign-diversity",
    "f3-interpretability",
    "f4-evaluation-thoroughness",
    "s1-concept-drift",
    "s2-active-attack",
    "s3-privacy",


]
metric_to_latex = {
    "f1-coverage": "F1",
    "f2-benign-diversity": "F2",
    "f3-interpretability": "F3",
    "f4-evaluation-thoroughness": "F4",
    "s1-concept-drift": "S1",
    "s2-active-attack": "S2",
    "s3-privacy": "S3",
}
latex_order = [metric_to_latex[m] for m in metric_keys]

category_mapping = {
    "feature-based": "Feature",
    "similarity-based": "Similarity",
    "identity-based": "Identity",
    "hybrid": "Hybrid",
    "unknown": "Unknown"
}

# Load data
with open("assessments.json", "r") as f:
    data = json.load(f)

category_metric_counts = defaultdict(lambda: defaultdict(Counter))
category_papers = defaultdict(set)
grand_metric_counts = defaultdict(Counter)
all_papers = set()

for paper, content in data.items():
    category_key = content.get("category", "unknown")
    display_category = category_mapping.get(category_key, category_key)
    all_papers.add(paper)
    category_papers[display_category].add(paper)
    for metric_json_key, metric_latex in zip(metric_keys, latex_order):
        val = content.get(metric_json_key)
        if isinstance(val, dict) and "manual" in val:
            verdict = val["manual"]
            category_metric_counts[display_category][metric_latex][verdict] += 1
            grand_metric_counts[metric_latex][verdict] += 1

def tex_bar(x, y, z, total):
    if total == 0:
        return "0 & 0 & 0 & 0"
    vals = [x, y, z]
    nums = [round(val * 100 / total) for val in vals]
    max_idx = max(range(3), key=lambda i: nums[i])
    out = []
    for i, n in enumerate(nums):
        if i == max_idx and n != 0:
            out.append(f"\\cellcolor{{gray!20}}{n}")
        else:
            out.append(str(n))
    return " & ".join(out)

with open("z_category.txt", "w") as out_file:
    # Header
    out_file.write("Category & Count & " + " & ".join(latex_order) + "\\\\\n")
    out_file.write("\\hline\n")

    for category in category_mapping.values():
        if category not in category_metric_counts:
            continue  # Skip unused categories
        row = [category, str(len(category_papers[category]))]
        num_unique = len(category_papers[category])
        for col in latex_order:
            counts = category_metric_counts[category][col]
            full = counts.get("High", 0)
            partial = counts.get("Medium", 0)
            non = counts.get("Low", 0)
            cell = tex_bar(full, partial, non, num_unique)
            row.append(cell)
        # row.append(str(num_unique))
        out_file.write("\\hline\n")
        out_file.write(" & ".join(row) + " \\\\\n")
    
    # Bold horizontal rule before Grand total
    out_file.write("\\hline\n")

    # Grand Total row
    row = ["Total", str(len(all_papers))]
    total_unique = len(all_papers)
    for col in latex_order:
        counts = grand_metric_counts[col]
        full = counts.get("High", 0)
        partial = counts.get("Medium", 0)
        non = counts.get("Low", 0)
        cell = tex_bar(full, partial, non, total_unique)
        row.append(cell)
    # row.append(str(total_unique))
    out_file.write(" & ".join(row) + " \\\\\n")

# --- JSON Output ---
json_dump = {}
for category in list(category_mapping.values()) + ["Total"]:
    if category == "Total":
        num_unique = len(all_papers)
        per_metric = {}
        for col in latex_order:
            counts = grand_metric_counts[col]
            full = counts.get("High", 0)
            partial = counts.get("Medium", 0)
            non = counts.get("Low", 0)
            # Percentages
            if num_unique > 0:
                full_pct = round(100.0 * full / num_unique, 2)
                partial_pct = round(100.0 * partial / num_unique, 2)
                non_pct = round(100.0 * non / num_unique, 2)
            else:
                full_pct = partial_pct = non_pct = 0.0
            per_metric[col] = {
                "High": full_pct,
                "Medium": partial_pct,
                "Low": non_pct,
                "counts": {
                    "High": full,
                    "Medium": partial,
                    "Low": non
                }
            }
        json_dump[category] = {
            "num_papers": num_unique,
            "metrics": per_metric
        }
    else:
        num_unique = len(category_papers[category])
        if num_unique == 0:
            continue
        per_metric = {}
        for col in latex_order:
            counts = category_metric_counts[category][col]
            full = counts.get("High", 0)
            partial = counts.get("Medium", 0)
            non = counts.get("Low", 0)
            if num_unique > 0:
                full_pct = round(100.0 * full / num_unique, 2)
                partial_pct = round(100.0 * partial / num_unique, 2)
                non_pct = round(100.0 * non / num_unique, 2)
            else:
                full_pct = partial_pct = non_pct = 0.0
            per_metric[col] = {
                "High": full_pct,
                "Medium": partial_pct,
                "Low": non_pct,
                "counts": {
                    "High": full,
                    "Medium": partial,
                    "Low": non
                }
            }
        json_dump[category] = {
            "num_papers": num_unique,
            "metrics": per_metric
        }

with open("category_table.json", "w") as jf:
    json.dump(json_dump, jf, indent=2)
