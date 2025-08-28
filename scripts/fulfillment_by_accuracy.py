import json
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
    vals = [int(x), int(y), int(z)]
    max_val = max(vals)
    def maybe_color(val, orig):
        return f"\\cellcolor{{gray!20}}{orig}" if val == max_val and max_val != 0 else orig
    return f"{maybe_color(vals[0], x)} & {maybe_color(vals[1], y)} & {maybe_color(vals[2], z)}"

# Define accuracy bins: list of tuples (low, high), high exclusive
bins = [
    (99, 100),
    (98, 99),
    (95, 98),
    (90, 95),
    (80, 90)
]
bin_labels = [
    "99--100",
    "98--99",
    "95--98",
    "90--95",
    "80--90",
    "<80",
    "N/A"
]

def get_accuracy_bin(acc_str):
    try:
        acc = float(acc_str)
        if acc < 1:
            acc *= 100
        for (low, high), label in zip(bins, bin_labels):
            if low <= acc < high:
                return label
        if acc < 80:
            return "<80"
        # If above 100, treat as highest bin
        return "99--100"
    except Exception:
        return "N/A"

# Load data
with open("assessments_new/assessments.json", "r") as f:
    data = json.load(f)

# Gather stats per accuracy bin
bin_metric_counts = defaultdict(lambda: defaultdict(Counter))
bin_papers = defaultdict(set)
grand_metric_counts = defaultdict(Counter)
all_papers = set()

for paper, content in data.items():
    acc_str = content.get("accuracy")
    bin_label = get_accuracy_bin(acc_str)
    bin_papers[bin_label].add(paper)
    all_papers.add(paper)
    for metric_json_key, metric_latex in zip(metric_keys, latex_order):
        val = content.get(metric_json_key)
        if isinstance(val, dict) and "manual" in val:
            verdict = val["manual"]
            bin_metric_counts[bin_label][metric_latex][verdict] += 1
            grand_metric_counts[metric_latex][verdict] += 1

# For ordering bins: high to low
ordered_bins = bin_labels  # as defined above

# ---- LaTeX output ----
with open("z_accuracy_table.txt", "w") as out_file:
    out_file.write("Accuracy & " + " & ".join(latex_order) + " \\\\\n")
    out_file.write("\\hline\n")
    for bin_label in ordered_bins:
        row = [bin_label]
        total_papers = len(bin_papers[bin_label]) or 1
        row.append(str(len(bin_papers[bin_label])))
        for col in latex_order:
            counts = bin_metric_counts[bin_label][col]
            full = counts.get("High", 0)
            partial = counts.get("Medium", 0)
            non = counts.get("Low", 0)
            full_pct = round(100.0 * full / total_papers)
            partial_pct = round(100.0 * partial / total_papers)
            non_pct = round(100.0 * non / total_papers)
            cell = tex_bar_highlight(f"{full_pct}", f"{partial_pct}", f"{non_pct}")
            row.append(cell)
        # row.append(str(len(bin_papers[bin_label])))
        out_file.write(" & ".join(row) + " \\\\\n")
    out_file.write("\\hline\n")
    # Grand total
    row = ["Grand total"]
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
for bin_label in ordered_bins + ["Grand total"]:
    if bin_label == "Grand total":
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
        json_dump[bin_label] = {
            "num_papers": len(all_papers),
            "metrics": per_metric
        }
    else:
        total_papers = len(bin_papers[bin_label]) or 1
        per_metric = {}
        for col in latex_order:
            counts = bin_metric_counts[bin_label][col]
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
        json_dump[bin_label] = {
            "num_papers": len(bin_papers[bin_label]),
            "metrics": per_metric
        }

with open("z_accuracy_table.json", "w") as jf:
    json.dump(json_dump, jf, indent=2)
