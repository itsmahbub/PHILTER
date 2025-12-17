import json
import numpy as np
from collections import defaultdict, Counter
from scipy.stats import chi2_contingency

target_key = "deployment_mode"  # server-side/client-side
input_file = "assessments.json"

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

# === Load data ===
with open(input_file, "r") as f:
    data = json.load(f)

# === Collect target groups ===
target_key_values = set()
for _, content in data.items():
    v = content.get(target_key)
    target_key_values.add(v if v is not None else "Unknown")
target_key_values = sorted(target_key_values, key=lambda x: str(x))

# === Count metrics per group ===
group_metric_counts = defaultdict(lambda: defaultdict(Counter))
group_papers = defaultdict(set)
all_papers = set()

for paper, content in data.items():
    group_val = content.get(target_key, "Unknown") or "Unknown"
    all_papers.add(paper)
    group_papers[group_val].add(paper)
    for metric_json_key, metric_latex in zip(metric_keys, latex_order):
        val = content.get(metric_json_key)
        if isinstance(val, dict) and "manual" in val:
            verdict = val["manual"]
            group_metric_counts[group_val][metric_latex][verdict] += 1

# === Perform χ² tests ===
results = {}
groups = list(group_metric_counts.keys())

for metric in latex_order:
    # Build contingency table: rows=groups, cols=[High, Medium, Low]
    table = []
    for g in groups:
        c = group_metric_counts[g][metric]
        row = [c.get("High", 0), c.get("Medium", 0), c.get("Low", 0)]
        table.append(row)
    table = np.array(table, dtype=int)

    # Skip if empty table
    if np.all(table == 0):
        continue

    # Drop columns (metrics) that are entirely zero across all groups
    col_sums = table.sum(axis=0)
    valid_cols = col_sums > 0
    if valid_cols.sum() < 2:  # need at least 2 columns with data
        print(f"Skipping {metric} (too few non-zero columns)")
        continue
    table = table[:, valid_cols]

    # Skip if identical distributions across groups
    if np.all(table[0] == table[1]):
        print(f"Skipping {metric} (identical distribution across groups)")
        continue

    try:
        chi2, p, dof, expected = chi2_contingency(table)
    except ValueError:
        print(f"Skipping {metric} (chi² failed)")
        continue

    results[metric] = {
        "chi2": float(chi2),
        "p_value": float(p),
        "degrees_of_freedom": int(dof),
        "expected_counts": expected.tolist(),
        "table": {
            g: {
                "High": int(table[i, 0]) if table.shape[1] > 0 else None,
                "Medium": int(table[i, 1]) if table.shape[1] > 1 else None,
                "Low": int(table[i, 2]) if table.shape[1] > 2 else None
            } for i, g in enumerate(groups)
        },
        "significant": bool(p < 0.05)
    }

# === Print Summary ===
print(f"{'Metric':<6} | {'Chi²':>8} | {'p-value':>10} | Significant")
print("-" * 42)
for m, v in results.items():
    chi2_val = v.get("chi2")
    p_val = v.get("p_value")
    sig = v.get("significant", False)
    chi2_str = f"{chi2_val:.2f}" if chi2_val is not None else "N/A"
    p_str = f"{p_val:.4f}" if p_val is not None else "N/A"
    print(f"{m:<6} | {chi2_str:>8} | {p_str:>10} | {sig}")

