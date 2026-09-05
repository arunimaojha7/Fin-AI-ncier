<<<<<<< HEAD
# Fin-AI-ncier
# AI Finance Controller

Automated bank-to-invoice reconciliation with evidence-based exception handling. Deterministic matching resolves the clear cases; AI investigation is reserved for the ones a rule engine genuinely can't decide.

## Problem

Reconciling bank transactions against invoices is still largely a manual process for most finance teams. Vendor name variations, timing differences, partial payments, and duplicate charges all break simple exact-match logic, forcing someone to manually dig through rows to figure out what happened. This doesn't scale as transaction volume grows, and manual reconciliation is slow and error-prone.

## Approach

A three-layer system:

1. **Deterministic rule engine** — matches bank transactions to invoices using fuzzy vendor-name matching (RapidFuzz), amount tolerance, and date proximity, producing a weighted confidence score and a margin (how much more confident the top match is than the next-best candidate).
2. **Confidence-based routing** — high-confidence, high-margin matches are auto-resolved with zero AI involvement. Only transactions the rule engine cannot confidently resolve are escalated.
3. **AI investigation layer** — Gemini investigates only the escalated cases, returning a structured verdict: exception type, severity, explanation, and recommended finance action.

## Architecture

```
Bank transactions + Invoices
            │
            ▼
     Rule Engine (RapidFuzz + weighted scoring)
            │
   ┌────────┼────────────┬─────────────┐
   ▼                     ▼             ▼
AUTO_MATCH          HUMAN_REVIEW   UNRESOLVED
(no AI needed)      (Gemini investigates ambiguous cases)
   │                     │             │
   └─────────────────────┴─────────────┘
                    │
                    ▼
        Exception Report + Dashboard
```

## Results

Measured on a synthetic batch of 104 bank transactions against 95 invoices, with deliberately injected discrepancies (vendor-name variations, amount mismatches, date mismatches, duplicates, missing invoices, partial payments, ambiguous vendors):

| Metric | Value |
|---|---|
| Records processed | 104 |
| Auto-matched (no AI) | 81 (78%) |
| Escalated — human review | 15 |
| Escalated — unresolved | 8 |
| Auto-match precision | 100.00% |
| Overall accuracy | 94.23% |

Of the 23 escalated transactions, only the genuinely ambiguous ones are sent to Gemini — the rest are resolved by typed rule-based logic (duplicate payment, partial payment, amount mismatch, date mismatch, missing invoice) without any API call.

## Why This Design

Routing every transaction through an LLM is unnecessary and expensive. Deterministic matching handles the ~78% of cases where the evidence is clear and auditable; Gemini is reserved for the minority of cases where rule-based confidence genuinely runs out. This keeps the system fast, cheap, and explainable — every automatic decision is traceable to a rule, and every AI decision comes with the model's own reasoning and a confidence signal, so low-confidence AI verdicts stay flagged for a human rather than auto-resolving silently.

## Tech Stack

- **Python, pandas** — data processing and pipeline logic
- **RapidFuzz** — fuzzy vendor-name matching
- **Faker** — synthetic transaction and invoice generation
- **Google Gemini API** — investigates ambiguous exceptions with structured JSON output
- **Streamlit** — interactive dashboard for exploring results and running live AI investigations

## How to Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your Gemini API key
export GEMINI_API_KEY="your-key-here"

# 3. Generate synthetic data
python src/data_generator.py

# 4. Inject realistic discrepancies
python src/data_corruptor.py

# 5. Run the reconciliation engine
python src/reconciliation_engine.py

# 6. Classify exceptions (rule-based + selective AI investigation)
python src/exception_classifier.py

# 7. Measure accuracy against ground truth
python src/evaluator.py

# 8. Launch the dashboard
streamlit run src/dashboard.py
```

## Project Structure

```
src/
  data_generator.py         # generates clean synthetic transactions and invoices
  data_corruptor.py         # injects realistic mismatches and edge cases
  reconciliation_engine.py  # fuzzy matching + confidence/margin scoring
  exception_classifier.py   # rule-based classification + Gemini investigation for ambiguous cases
  evaluator.py               # accuracy measurement against ground truth
  dashboard.py                # Streamlit UI for exploring results
data/                         # generated and output CSVs
tests/                        # unit tests
requirements.txt
```

## Honest Limitations / What We'd Add With More Time

- Currently validated on a single synthetic batch; would benefit from testing across multiple random seeds and larger volumes (500+ records) to confirm accuracy holds
- Single-currency only; no handling of multi-currency or FX-adjusted amounts
- No retry/caching layer for Gemini calls — a failed API call currently falls back to a safe default rather than retrying
- No persistent storage; results are recomputed from CSVs on each run rather than stored in a database
- Confidence thresholds for routing to human review vs. AI investigation are manually tuned, not learned from labeled data
=======
# AI Finance Controller

### Run the books and the cash position

An AI-powered finance operations system that reconciles bank transactions against invoices, detects exceptions, measures reconciliation accuracy, and uses Gemini AI to investigate difficult cases that deterministic rules cannot confidently resolve.

---

## 🚀 Why This Project?

Financial reconciliation is often repetitive and rule-heavy:

- Does this bank transaction correspond to an invoice?
- Is the vendor name slightly different?
- Is the payment amount correct?
- Is the payment late or early?
- Is this a duplicate?
- Is this a partial payment?
- Should a human investigate the transaction?

A simple matching system can produce matches, but a finance controller needs more than that.

This project focuses on:

> **Throughput + measured accuracy + explainable exceptions + AI-assisted investigation**

The system processes a batch of synthetic financial records and reports both successful matches and cases requiring human attention.

---

# 🏗️ Architecture

```text
                 ┌──────────────────┐
                 │  Data Generator   │
                 │  Synthetic Data   │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │    Corruptor      │
                 │ Introduce Errors  │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Reconciliation   │
                 │     Engine       │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Exception        │
                 │ Classifier       │
                 └────────┬─────────┘
                          │
             ┌────────────┴────────────┐
             │                         │
             ▼                         ▼
      Deterministic Rules        Gemini AI Review
             │                         │
             └────────────┬────────────┘
                          ▼
                 ┌──────────────────┐
                 │    Evaluator      │
                 │ Accuracy Metrics  │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Streamlit        │
                 │   Dashboard      │
                 └──────────────────┘
>>>>>>> 089e6ef57916724e58ec03027af4e913441c1400
