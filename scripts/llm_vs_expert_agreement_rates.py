import json

# Metric mapping
metric_map = {
    "f1-coverage": "F1. Diversity of Phishing Tactics",
    "f2-benign-diversity": "F2. Diversity of Benign Pages",
    "f3-interpretability": "F3. Interpretability",
    "f4-evaluation-thoroughness": "F4. Evaluation Transparency",

    "s1-concept-drift": "S1. Adaptation to Concept Drift",
    "s2-active-attack": "S2. Resistance to Active Attacks",
    "s3-privacy": "S3. Privacy Preservation"

}

metric_order = [
    "f1-coverage",
    "f2-benign-diversity",
    "f3-interpretability",
    "f4-evaluation-thoroughness",
    "s1-concept-drift",
    "s2-active-attack",
    "s3-privacy"

]

def load_data(filename):
    with open(filename, "r") as f:
        return json.load(f)

def get_verdict(d, key):
    if isinstance(d, dict):
        return d.get(key, d)
    return d

def match(v1, v2):
    return str(v1).strip().lower() == str(v2).strip().lower()

def compute_agreement(data, llm_field):
    counts = {k: [0, 0] for k in metric_map}  # metric: [match, total]
    for paper, paper_info in data.items():
        for metric in metric_map:
            if metric in paper_info:
                mval = paper_info[metric]
                manual = mval.get("manual", None)
                llm = mval.get(llm_field, None)
                manual_verdict = manual
                llm_verdict = get_verdict(llm, 'value') if llm else None
                if manual_verdict and llm_verdict and manual_verdict not in ["-", ""]:
                    counts[metric][1] += 1
                    if match(manual_verdict, llm_verdict):
                        counts[metric][0] += 1
    return {k: (v[0], v[1], (v[0] / v[1] * 100) if v[1] else 0) for k, v in counts.items()}

def latex_line(metric, count, total, percentage):
    return f"{metric_map[metric]}  & {count}/{total} ({percentage:.2f}\\%) \\\\"

def main():
    data = load_data("assessments.json")

  
    results_llm = compute_agreement(data, "arbitrator")

    out_lines = []
    out_lines.append("\\begin{tabular}{lr}")
    out_lines.append("\\toprule")
    out_lines.append("Metric & Agreement \\\\")
    out_lines.append("\\midrule")
    overall_match = 0
    overall_total = 0
    for metric in metric_order:
        count, total, percentage = results_llm[metric]
        overall_match += count
        overall_total += total
        out_lines.append(latex_line(metric, count, total, percentage))
    
    out_lines.append("\\midrule")
    overall_percentage = (overall_match / overall_total * 100)
    out_lines.append(f"\\textbf{{Overall}} & {overall_match}/{overall_total} ({overall_percentage:.2f}\\%) \\\\")

    out_lines.append("\\bottomrule")
    out_lines.append("\\end{tabular}")

  
    for line in out_lines:
        print(line)

if __name__ == "__main__":
    main()
