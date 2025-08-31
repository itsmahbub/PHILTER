# PHILTER

**PH**ishing detection literature **I**nspection via **L**LMs and **T**argeted **E**xpert **R**eview.

PHILTER is a transparent, scalable framework for assessing AI-based phishing website detection papers against seven deployment-relevant requirements: four **Functionality** metrics (F1–F4) and three **Security** metrics (S1–S3). LLMs extract evidence and draft rationales; **experts validate and finalize all labels**. Applying PHILTER to 55 studies reveals systemic gaps and trade-offs.

---

## Framework Overview

![Framework Overview](framework-overview.png)

## 📦 Repository layout

PHILTER/
├─ codebook/
│  ├─ f1-coverage.txt
│  ├─ f2-benign-diversity.txt
│  ├─ f3-interpretability.txt
│  ├─ f4-evaluation-thoroughness.txt
│  ├─ s1-concept-drift.txt
│  ├─ s2-active-attack.txt
│  └─ s3-privacy.txt
├─ llm_responses/
├─ papers/
├─ scripts/
│  ├─ assessments_table_expert.py
│  ├─ fulfillment_by_accuracy.py
│  ├─ fulfillment_by_category.py
│  ├─ fulfillment_by_citation.py
│  ├─ fulfillment_by_deployment_mode.py
│  ├─ fulfillment_by_detection_mode.py
│  ├─ fulfillment_by_input.py
│  ├─ fulfillment_by_publication_year.py
│  ├─ llm_vs_expert_agreement_rates.py
│  └─ llm_vs_expert_assessments.py
├─ llm_assessment_pipeline.py
├─ assessments.json # Contains LLM assessments and expert assessments
├─ README.md
└─ requirements.txt


## Quick start

Put the research papers on phishing website detection inside `papers` directory.

```bash
# 1) Create env (Python 3.10–3.12 recommended)
python -m venv .venv && source .venv/bin/activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Set OpenAI and Gemini API keys
export OPENAI_API_KEY=...
export GOOGLE_API_KEY=...

# 4) Run LLM-assisted prelimiary evaluation stage
python llm_assessment_pipeline.py -p . -m codebook/f1-coverage.txt -o assessments.json
```
