import json
from collections import defaultdict, Counter
target_key = "deployment_mode"

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

# Load data
with open("assessments.json", "r") as f:
    data = json.load(f)

target_key_values = set()
for paper, content in data.items():
    target_key_val = content.get(f"{target_key}", None)
    target_key_values.add(target_key_val if target_key_val is not None else "Unknown")
target_key_values = sorted(target_key_values, key=lambda x: str(x))  # sort for consistency

# Prepare counters
realtime_metric_counts = defaultdict(lambda: defaultdict(Counter))
realtime_papers = defaultdict(set)
grand_metric_counts = defaultdict(Counter)
all_papers = set()

for paper, content in data.items():
    realtime_key = content.get(f"{target_key}", None)
    if realtime_key is None:
        realtime_key = "Unknown"
    all_papers.add(paper)
    realtime_papers[realtime_key].add(paper)
    for metric_json_key, metric_latex in zip(metric_keys, latex_order):
        val = content.get(metric_json_key)
        if isinstance(val, dict) and "manual" in val:
            verdict = val["manual"]
            realtime_metric_counts[realtime_key][metric_latex][verdict] += 1
            grand_metric_counts[metric_latex][verdict] += 1

def tex_bar_highlight(x, y, z):
    vals = [int(x), int(y), int(z)]
    max_val = max(vals)
    def maybe_color(val, orig):
        return f"\\cellcolor{{gray!20}}{orig}" if val == max_val and max_val != 0 else orig
    return f"{maybe_color(vals[0], x)} & {maybe_color(vals[1], y)} & {maybe_color(vals[2], z)}"

with open(f"{target_key}.txt", "w") as out_file:
    # Header
    out_file.write(f"{target_key} & Count & " + " & ".join(latex_order) + " \\\\\n")
    out_file.write("\\hline\n")

    for rt_group in target_key_values:
        row = [str(rt_group), str(len(realtime_papers[rt_group]))]
        total_papers = len(realtime_papers[rt_group]) or 1  # avoid division by zero
        for col in latex_order:
            counts = realtime_metric_counts[rt_group][col]
            full = counts.get("High", 0)
            partial = counts.get("Medium", 0)
            non = counts.get("Low", 0)
            # Percentages, no percent sign in cell
            full_pct = round(100.0 * full / total_papers)
            partial_pct = round(100.0 * partial / total_papers)
            non_pct = round(100.0 * non / total_papers)
            cell = tex_bar_highlight(f"{full_pct}", f"{partial_pct}", f"{non_pct}")
            row.append(cell)
        num_unique = len(realtime_papers[rt_group])
        # row.append(str(num_unique))
        out_file.write(" & ".join(row) + " \\\\\n")

    # Bold horizontal rule before Grand total
    out_file.write("\\hline\n")

    # Grand Total row
    row = ["Total"]
    total_papers = len(all_papers) or 1
    for col in latex_order:
        counts = grand_metric_counts[col]
        full = counts.get("High", 0)
        partial = counts.get("Medium", 0)
        non = counts.get("Low", 0)
        full_pct = round(100.0 * full / total_papers)
        partial_pct = round(100.0 * partial / total_papers)
        non_pct = round(100.0 * non / total_papers)
        cell = tex_bar_highlight(f"{full_pct}", f"{partial_pct}", f"{non_pct}")
        row.append(cell)
    # row.append(str(total_papers))
    out_file.write(" & ".join(row) + " \\\\\n")
