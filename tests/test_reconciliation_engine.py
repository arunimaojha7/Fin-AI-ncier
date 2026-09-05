"""
Tests for src/reconciliation_engine.py

Run from the project root with:
    pytest tests/
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

# Make src/ importable when running pytest from the project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from reconciliation_engine import (
    normalize_vendor,
    vendor_similarity,
    amount_score,
    date_score,
    calculate_score,
    classify_match,
    find_best_match,
)


# ============================================================
# normalize_vendor
# ============================================================

def test_normalize_vendor_strips_common_suffixes():
    assert normalize_vendor("Accenture Pvt Ltd") == "accenture"
    assert normalize_vendor("Infosys Ltd") == "infosys"


def test_normalize_vendor_handles_nan():
    assert normalize_vendor(float("nan")) == ""


def test_normalize_vendor_is_case_insensitive():
    assert normalize_vendor("GOOGLE INDIA") == normalize_vendor("google india")


# ============================================================
# vendor_similarity
# ============================================================

def test_vendor_similarity_identical_names_scores_100():
    assert vendor_similarity("Infosys", "Infosys") == 100


def test_vendor_similarity_known_variation_scores_high():
    # "TCS" vs "Tata Consultancy Services" is a real corruption case
    # in data_corruptor.py — abbreviations won't score perfectly,
    # but should still be closer than an unrelated vendor.
    close = vendor_similarity("Amazon AWS", "Amazon Web Services")
    unrelated = vendor_similarity("Amazon AWS", "Wipro")
    assert close > unrelated


# ============================================================
# amount_score
# ============================================================

def test_amount_score_exact_match_is_100():
    assert amount_score(1000, 1000) == 100


def test_amount_score_small_difference_scores_high():
    # 1% difference should still score 95 per the tiered logic
    assert amount_score(1010, 1000) == 95


def test_amount_score_large_difference_scores_zero():
    assert amount_score(2000, 1000) == 0


def test_amount_score_handles_zero_invoice_amount():
    assert amount_score(100, 0) == 0


# ============================================================
# date_score
# ============================================================

def test_date_score_same_day_is_100():
    assert date_score("2026-08-01", "2026-08-01") == 100


def test_date_score_within_two_days_scores_90():
    assert date_score("2026-08-03", "2026-08-01") == 90


def test_date_score_far_apart_scores_zero():
    assert date_score("2026-09-01", "2026-08-01") == 0


# ============================================================
# calculate_score (weighted combination)
# ============================================================

def test_calculate_score_perfect_match_is_100():
    bank_row = {"vendor": "Infosys", "amount": 1000, "date": "2026-08-01"}
    invoice_row = {"vendor": "Infosys", "amount": 1000, "date": "2026-08-01"}
    assert calculate_score(bank_row, invoice_row) == 100.0


def test_calculate_score_completely_unrelated_is_low():
    bank_row = {"vendor": "Random Vendor Co", "amount": 999999, "date": "2020-01-01"}
    invoice_row = {"vendor": "Infosys", "amount": 1000, "date": "2026-08-01"}
    assert calculate_score(bank_row, invoice_row) < 40


# ============================================================
# classify_match (routing logic — the core business decision)
# ============================================================

def test_classify_match_high_score_high_margin_is_auto_match():
    assert classify_match(score=95, margin=20) == "AUTO_MATCH"


def test_classify_match_high_score_low_margin_is_human_review():
    # This is the "confident but ambiguous" case — the smart part
    # of the design. Must NOT silently auto-resolve.
    assert classify_match(score=90, margin=2) == "HUMAN_REVIEW"


def test_classify_match_medium_score_is_human_review():
    assert classify_match(score=70, margin=10) == "HUMAN_REVIEW"


def test_classify_match_low_score_is_unresolved():
    assert classify_match(score=30, margin=0) == "UNRESOLVED"


def test_classify_match_boundary_at_85_is_auto_match():
    assert classify_match(score=85, margin=10) == "AUTO_MATCH"


def test_classify_match_boundary_just_below_85_is_human_review():
    assert classify_match(score=84.9, margin=10) == "HUMAN_REVIEW"


# ============================================================
# find_best_match (end-to-end on a tiny synthetic set)
# ============================================================

def test_find_best_match_picks_the_closer_invoice():
    bank_row = pd.Series(
        {"vendor": "Infosys", "amount": 1000, "date": "2026-08-01"}
    )

    invoices = pd.DataFrame([
        {"invoice_id": "INV-1", "vendor": "Infosys", "amount": 1000, "date": "2026-08-01"},
        {"invoice_id": "INV-2", "vendor": "Wipro", "amount": 50, "date": "2020-01-01"},
    ])

    best_invoice, score, margin = find_best_match(bank_row, invoices)

    assert best_invoice["invoice_id"] == "INV-1"
    assert score == 100.0
    assert margin > 0  # the correct match should clearly beat the wrong one


def test_find_best_match_returns_none_for_empty_invoices():
    bank_row = pd.Series(
        {"vendor": "Infosys", "amount": 1000, "date": "2026-08-01"}
    )
    invoices = pd.DataFrame(columns=["invoice_id", "vendor", "amount", "date"])

    best_invoice, score, margin = find_best_match(bank_row, invoices)

    assert best_invoice is None
    assert score == 0
    assert margin == 0
    