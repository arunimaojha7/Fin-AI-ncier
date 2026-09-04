# AI Finance Controller

## Problem
[2-3 sentences: reconciliation between bank transactions and invoices is manual, 
slow, and error-prone at scale. Vendor name variations, timing differences, 
partial payments, and duplicates make exact matching insufficient.]

## Approach
A three-layer system:
1. **Deterministic rule engine** — fuzzy-matches bank transactions to invoices 
   using vendor name similarity (RapidFuzz), amount tolerance, and date proximity, 
   producing a weighted confidence score.
2. **Confidence-based routing** — high-confidence matches are auto-resolved with 
   zero AI involvement; only genuinely ambiguous cases are escalated.
3. **AI investigation layer** — Claude investigates only the cases the rule engine 
   can't confidently resolve, returning a structured, explained verdict.

## Architecture
[Paste a simple text diagram, e.g.]