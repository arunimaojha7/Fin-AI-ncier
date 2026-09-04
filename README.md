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
