# Fin-AI-ncier — AI Finance Controller

Automated bank-to-invoice reconciliation with evidence-based exception handling. Deterministic matching resolves the clear cases; AI investigation is reserved for the ones a rule engine genuinely can't decide.

## Problem

Reconciling bank transactions against invoices is still largely a manual process for most finance teams. Vendor name variations, timing differences, partial payments, and duplicate charges all break simple exact-match logic, forcing someone to manually dig through rows to figure out what happened. This doesn't scale as transaction volume grows, and manual reconciliation is slow and error-prone.

## Approach

A three-layer system:

1. **Deterministic rule engine** — matches bank transactions to invoices using fuzzy vendor-name matching (RapidFuzz), amount tolerance, and date proximity, producing a weighted confidence score and a margin (how much more confident the top match is than the next-best candidate).
2. **Confidence-based routing** — high-confidence, high-margin matches are auto-resolved with zero AI involvement. Only transactions the rule engine cannot confidently resolve are escalated.
3. **AI investigation layer** — Gemini investigates only the escalated cases, returning a structured verdict: exception type, severity, explanation, and recommended finance action.

## Architecture

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
      (AUTO_MATCH, no AI)     (HUMAN_REVIEW / UNRESOLVED)
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

## Robustness Validation

The pipeline was tested across multiple independently randomized synthetic batches (different seeds, different corruption patterns):

| Seed | Records | Auto-Matched | Auto-Match Precision | Overall Accuracy |
|------|---------|---------------|----------------------|-------------------|
| 42   | 104     | 81 (78%)      | 100.00%              | 94.23%            |
| 500  | 104     | 78 (75%)      | 100.00%              | 93.27%            |

Auto-match precision remained perfect (zero incorrect automatic matches) across runs, and overall accuracy stayed within a ~1 point range — indicating the matching logic generalizes rather than being tuned to one specific dataset.

## Why This Design

Routing every transaction through an LLM is unnecessary and expensive. Deterministic matching handles the ~78% of cases where the evidence is clear and auditable; Gemini is reserved for the minority of cases where rule-based confidence genuinely runs out. This keeps the system fast, cheap, and explainable — every automatic decision is traceable to a rule, and every AI decision comes with the model's own reasoning and a confidence signal, so low-confidence AI verdicts stay flagged for a human rather than auto-resolving silently.

## Tech Stack

- **Python, pandas** — data processing and pipeline logic
- **RapidFuzz** — fuzzy vendor-name matching
- **Faker** — synthetic transaction and invoice generation
- **Google Gemini API** — investigates ambiguous exceptions with structured JSON output
- **Streamlit** — interactive dashboard for exploring results and running live AI investigations
- **pytest** — unit tests for matching logic and AI fallback behavior

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

# Optional: run the test suite
pytest tests/ -v
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

- Validated across two independently randomized synthetic batches (see Robustness Validation above); would benefit from testing across more seeds and larger volumes (500+ records) to further confirm stability
- Single-currency only; no handling of multi-currency or FX-adjusted amounts
- No retry/caching layer for Gemini calls — a failed API call currently falls back to a safe default rather than retrying
- No persistent storage; results are recomputed from CSVs on each run rather than stored in a database
- Confidence thresholds for routing to human review vs. AI investigation are manually tuned, not learned from labeled data