import json
import re
from collections import defaultdict, Counter

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

def tex_bar_highlight(x, y, z):
    x_num = int(float(x.replace("", "")))
    y_num = int(float(y.replace("", "")))
    z_num = int(float(z.replace("", "")))
    max_val = max(x_num, y_num, z_num)
    def color(val, v):
        return f"\\cellcolor{{gray!20}}{v}" if val == max_val and max_val != 0 else v
    x_col = color(x_num, x)
    y_col = color(y_num, y)
    z_col = color(z_num, z)
    return f"{x_col} & {y_col} & {z_col}"

def get_citation_bucket(citation_str):
    if citation_str is None:
        return "unknown"
    try:
        citation_str = str(citation_str).strip()
        if not citation_str:
            return "unknown"
        match = re.search(r"[\d.]+", citation_str)
        if not match:
            return "unknown"
        citation = float(match.group(0))
    except Exception:
        return "unknown"
    if citation < 20:
        return "\\textless 20"
    elif citation < 50:
        return "20--50"
    elif citation < 100:
        return "50--100"
    elif citation < 200:
        return "100--200"
    else:
        return "\\textgreater 200"

# Load data
with open("assessments.json", "r") as f:
    data = json.load(f)

bucket_metric_counts = defaultdict(lambda: defaultdict(Counter))
bucket_papers = defaultdict(set)
grand_metric_counts = defaultdict(Counter)
all_papers = set()
buckets_present = set()

for paper, content in data.items():
    citation_str = content.get("citation_count")
    bucket = get_citation_bucket(citation_str)
    buckets_present.add(bucket)
    bucket_papers[bucket].add(paper)
    all_papers.add(paper)
    for metric_json_key, metric_latex in zip(metric_keys, latex_order):
        val = content.get(metric_json_key)
        if isinstance(val, dict) and "manual" in val:
            verdict = val["manual"]
            bucket_metric_counts[bucket][metric_latex][verdict] += 1
            grand_metric_counts[metric_latex][verdict] += 1

bucket_order = ["\\textgreater 200", "100--200", "50--100", "20--50", "\\textless 20"]
sorted_buckets = [b for b in bucket_order if b in buckets_present]
if "unknown" in buckets_present:
    sorted_buckets.append("unknown")

with open("citation_table.txt", "w") as out_file:
    out_file.write("Citations & Count & " + " & ".join(latex_order) + " \\\\\n")
    out_file.write("\\hline\n")
    for bucket in sorted_buckets:
        row = [bucket, str(len(bucket_papers[bucket]))]
        total_papers = len(bucket_papers[bucket]) or 1
        for col in latex_order:
            counts = bucket_metric_counts[bucket][col]
            full = counts.get("High", 0)
            partial = counts.get("Medium", 0)
            non = counts.get("Low", 0)
            full_pct = 100.0 * full / total_papers
            partial_pct = 100.0 * partial / total_papers
            non_pct = 100.0 * non / total_papers
            full_str = f"{full_pct:.0f}"
            partial_str = f"{partial_pct:.0f}"
            non_str = f"{non_pct:.0f}"
            cell = tex_bar_highlight(full_str, partial_str, non_str)
            row.append(cell)
        # row.append(str(total_papers))
        out_file.write(" & ".join(row) + " \\\\\n")
    out_file.write("\\hline\n")
    # Grand total row
    row = ["Grand total"]
    total_papers = len(all_papers) or 1
    for col in latex_order:
        counts = grand_metric_counts[col]
        full = counts.get("High", 0)
        partial = counts.get("Medium", 0)
        non = counts.get("Low", 0)
        full_pct = 100.0 * full / total_papers
        partial_pct = 100.0 * partial / total_papers
        non_pct = 100.0 * non / total_papers
        full_str = f"{full_pct:.0f}"
        partial_str = f"{partial_pct:.0f}"
        non_str = f"{non_pct:.0f}"
        cell = tex_bar_highlight(full_str, partial_str, non_str)
        row.append(cell)
    # row.append(str(total_papers))
    out_file.write(" & ".join(row) + " \\\\\n")

# ------- JSON dump section --------
json_dump = {}
for bucket in sorted_buckets + ["Grand total"]:
    if bucket == "Grand total":
        total_papers = len(all_papers) or 1
        per_metric = {}
        for col in latex_order:
            counts = grand_metric_counts[col]
            full = counts.get("High", 0)
            partial = counts.get("Medium", 0)
            non = counts.get("Low", 0)
            full_pct = 100.0 * full / total_papers
            partial_pct = 100.0 * partial / total_papers
            non_pct = 100.0 * non / total_papers
            per_metric[col] = {
                "High": round(full_pct, 2),
                "Medium": round(partial_pct, 2),
                "Low": round(non_pct, 2),
                "counts": {
                    "High": full,
                    "Medium": partial,
                    "Low": non
                }
            }
        json_dump[bucket] = {
            "num_papers": len(all_papers),
            "metrics": per_metric
        }
    else:
        total_papers = len(bucket_papers[bucket]) or 1
        per_metric = {}
        for col in latex_order:
            counts = bucket_metric_counts[bucket][col]
            full = counts.get("High", 0)
            partial = counts.get("Medium", 0)
            non = counts.get("Low", 0)
            full_pct = 100.0 * full / total_papers
            partial_pct = 100.0 * partial / total_papers
            non_pct = 100.0 * non / total_papers
            per_metric[col] = {
                "High": round(full_pct, 2),
                "Medium": round(partial_pct, 2),
                "Low": round(non_pct, 2),
                "counts": {
                    "High": full,
                    "Medium": partial,
                    "Low": non
                }
            }
        json_dump[bucket] = {
            "num_papers": len(bucket_papers[bucket]),
            "metrics": per_metric
        }

with open("citation_table.json", "w") as jf:
    json.dump(json_dump, jf, indent=2)
