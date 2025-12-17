import json
import numpy as np
from scipy.stats import chi2_contingency

# === Load aggregated category data ===
try:
    with open("category_table.json", "r") as f:
        data = json.load(f)
except:
    print("Please run `python scripts/fulfillment_by_category.py` first, which will generate `category_table.json`")
    exit(1)

# Categories and metrics
categories = list(data.keys())
metrics = list(next(iter(data.values()))["metrics"].keys())

results = {}

for metric in metrics:
    # Build contingency table: rows = categories, cols = [High, Medium, Low]
    table = []
    for category in categories:
        counts = data[category]["metrics"][metric]["counts"]
        row = [
            counts.get("High", 0),
            counts.get("Medium", 0),
            counts.get("Low", 0),
        ]
        table.append(row)

    table = np.array(table, dtype=int)

    # Skip if table is entirely empty
    if np.all(table == 0):
        print(f"Skipping {metric}: all zeros")
        continue

    # Drop outcome columns with zero total count
    col_sums = table.sum(axis=0)
    valid_cols = col_sums > 0
    if valid_cols.sum() < 2:
        print(f"Skipping {metric}: too few non-zero outcome levels")
        continue
    table = table[:, valid_cols]

    # Run chi-square test (Pearson)
    try:
        chi2, p, dof, expected = chi2_contingency(table)
    except ValueError:
        print(f"Skipping {metric}: chi-square failed")
        continue

    results[metric] = {
        "chi2": float(chi2),
        "p_value": float(p),
        "degrees_of_freedom": int(dof),
        "significant": bool(p < 0.05),
    }

# === Print summary ===
print(f"{'Metric':<6} | {'Chi²':>8} | {'p-value':>10} | Significant")
print("-" * 42)

for metric, v in results.items():
    print(
        f"{metric:<6} | "
        f"{v['chi2']:>8.2f} | "
        f"{v['p_value']:>10.4f} | "
        f"{v['significant']}"
    )
