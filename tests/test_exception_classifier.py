"""
Tests for src/exception_classifier.py

These focus on the fallback path (no API key / AI unavailable), since
that's the part that must behave safely without making a real network
call in CI or on a machine without GEMINI_API_KEY set.

Run from the project root with:
    pytest tests/
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from exception_classifier import ask_gemini_to_review


def test_ask_gemini_falls_back_gracefully_without_api_key(monkeypatch):
    # Simulate a machine/CI run with no GEMINI_API_KEY set.
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    bank_row = {"bank_id": "BANK-T0001", "bank_vendor": "Infosys", "bank_amount": 1000}
    invoice = {"invoice_id": "INV-T0001", "vendor": "Infosys", "amount": 1000}

    result = ask_gemini_to_review(bank_row, invoice, score=70, margin=3)

    # Must return a well-formed dict, never raise or crash the pipeline.
    assert isinstance(result, dict)
    assert result["exception_type"] == "AI_UNAVAILABLE"
    assert result["risk"] == "HIGH"
    assert "recommendation" in result
    assert "recommended_action" in result


def test_ask_gemini_fallback_always_flags_for_human_review(monkeypatch):
    # Whatever else changes, an unavailable AI must never silently
    # auto-approve a transaction — it should always defer to a human.
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    result = ask_gemini_to_review(
        {"bank_id": "BANK-X"}, None, score=0, margin=0
    )

    assert result["recommendation"] != "AUTO_MATCH"