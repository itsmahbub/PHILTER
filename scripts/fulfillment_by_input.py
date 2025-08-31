import json
from collections import defaultdict, Counter

mapping = {
    "URL": "U",
    "Webpage Content": "C",
    "External Metadata": "M",
    "URL, External Metadata": "U, M",
    "URL, Webpage Content": "U, C",
    "URL, Webpage Content, External Metadata": "U, C, M",
}

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
    vals = [int(x), int(y), int(z)]
    max_val = max(vals)
    # In case all are zero, don't highlight
    def maybe_color(val, orig):
        return f"\\cellcolor{{gray!20}}{orig}" if val == max_val and max_val != 0 else orig
    return f"{maybe_color(vals[0], x)} & {maybe_color(vals[1], y)} & {maybe_color(vals[2], z)}"

# Load data
with open("assessments.json", "r") as f:
    data = json.load(f)

input_metric_counts = defaultdict(lambda: defaultdict(Counter))
input_papers = defaultdict(set)
grand_metric_counts = defaultdict(Counter)
all_papers = set()
inputs_present = set()

for paper, content in data.items():
    input_type = content.get("Input")
    if not input_type or not isinstance(input_type, str):
        input_type = "unknown"
    inputs_present.add(input_type)
    input_papers[input_type].add(paper)
    all_papers.add(paper)
    for metric_json_key, metric_latex in zip(metric_keys, latex_order):
        val = content.get(metric_json_key)
        if isinstance(val, dict) and "manual" in val:
            verdict = val["manual"]
            input_metric_counts[input_type][metric_latex][verdict] += 1
            grand_metric_counts[metric_latex][verdict] += 1

sorted_inputs = sorted([i for i in inputs_present if i != "unknown"])
if "unknown" in inputs_present:
    sorted_inputs.append("unknown")

with open("input_table.txt", "w") as out_file:
    out_file.write("Input & " + " & ".join(latex_order) + " \\\\\n")
    out_file.write("\\hline\n")
    for input_type in sorted_inputs:
        row = [mapping.get(input_type, input_type), str(len(input_papers[input_type]))]
        total_papers = len(input_papers[input_type]) or 1  # avoid division by zero
        for col in latex_order:
            counts = input_metric_counts[input_type][col]
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
    out_file.write("\\hline\n")
    # Total row
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

# ---- JSON output ----
json_dump = {}
for input_type in sorted_inputs + ["Total"]:
    if input_type == "Total":
        total_papers = len(all_papers) or 1
        per_metric = {}
        for col in latex_order:
            counts = grand_metric_counts[col]
            full = counts.get("High", 0)
            partial = counts.get("Medium", 0)
            non = counts.get("Low", 0)
            full_pct = round(100.0 * full / total_papers, 2)
            partial_pct = round(100.0 * partial / total_papers, 2)
            non_pct = round(100.0 * non / total_papers, 2)
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
        json_dump[input_type] = {
            "num_papers": len(all_papers),
            "metrics": per_metric
        }
    else:
        total_papers = len(input_papers[input_type]) or 1
        per_metric = {}
        for col in latex_order:
            counts = input_metric_counts[input_type][col]
            full = counts.get("High", 0)
            partial = counts.get("Medium", 0)
            non = counts.get("Low", 0)
            full_pct = round(100.0 * full / total_papers, 2)
            partial_pct = round(100.0 * partial / total_papers, 2)
            non_pct = round(100.0 * non / total_papers, 2)
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
        json_dump[mapping.get(input_type, input_type)] = {
            "num_papers": len(input_papers[input_type]),
            "metrics": per_metric
        }

with open("z_input_table.json", "w") as jf:
    json.dump(json_dump, jf, indent=2)
