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

# Load data
with open("assessments_new/assessments.json", "r") as f:
    data = json.load(f)

# Assign all years to int, map <2019 to '<2019'
paper_year_map = {}
years = set()
for paper, content in data.items():
    yr = content.get("year")
    if yr is None:
        continue
    try:
        yr = int(yr)
    except Exception:
        continue
    mapped_year = yr if yr >= 2019 else "<2019"
    paper_year_map[paper] = mapped_year
    years.add(mapped_year)

# Sort: descending years, then "<2019" last
year_list = [y for y in years if y != "<2019"]
year_list = sorted(year_list, reverse=True)
if "<2019" in years:
    year_list.append("<2019")

# Gather stats per year
year_metric_counts = defaultdict(lambda: defaultdict(Counter))
year_papers = defaultdict(set)
grand_metric_counts = defaultdict(Counter)
all_papers = set()

for paper, content in data.items():
    mapped_year = paper_year_map.get(paper)
    if mapped_year is None:
        continue
    year_papers[mapped_year].add(paper)
    all_papers.add(paper)
    for metric_json_key, metric_latex in zip(metric_keys, latex_order):
        val = content.get(metric_json_key)
        if isinstance(val, dict) and "manual" in val:
            verdict = val["manual"]
            year_metric_counts[mapped_year][metric_latex][verdict] += 1
            grand_metric_counts[metric_latex][verdict] += 1

# ---- LaTeX output ----
with open("z_year_table.txt", "w") as out_file:
    out_file.write("Year & Count & " + " & ".join(latex_order) + " & Total \\\\\n")
    out_file.write("\\hline\n")
    for year in year_list:
        row = [str(year), str(len(year_papers[year]))]
        total_papers = len(year_papers[year]) or 1  # Avoid div by zero
        for col in latex_order:
            counts = year_metric_counts[year][col]
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
    # Bold horizontal rule before Grand total
    out_file.write("\\hline\n")
    # Grand Total row
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
for year in year_list + ["Grand total"]:
    if year == "Grand total":
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
        json_dump[str(year)] = {
            "num_papers": len(all_papers),
            "metrics": per_metric
        }
    else:
        total_papers = len(year_papers[year]) or 1
        per_metric = {}
        for col in latex_order:
            counts = year_metric_counts[year][col]
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
        json_dump[str(year)] = {
            "num_papers": len(year_papers[year]),
            "metrics": per_metric
        }

with open("z_year_table.json", "w") as jf:
    json.dump(json_dump, jf, indent=2)
