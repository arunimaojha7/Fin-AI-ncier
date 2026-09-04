import os
import json
from pathlib import Path

import pandas as pd
from google import genai


# ==================================================
# PATHS
# ==================================================

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


# ==================================================
# GEMINI SETTINGS
# ==================================================

GEMINI_MODEL = "gemini-3.7-flash"


# ==================================================
# LOAD DATA
# ==================================================

def load_data():

    results = pd.read_csv(
        DATA_DIR / "reconciliation_results.csv"
    )

    invoices = pd.read_csv(
        DATA_DIR / "messy_invoices.csv"
    )

    return results, invoices


# ==================================================
# GEMINI AI REVIEW
# ==================================================

def ask_gemini_to_review(
    bank_row,
    invoice,
    score,
    margin
):

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:

        return {
            "recommendation": "REVIEW",
            "reason": "Gemini API key is missing.",
            "exception_type": "AI_UNAVAILABLE",
            "recommended_action":
                "Human finance review required.",
            "risk": "HIGH"
        }

    print("Gemini API key detected:", bool(api_key))
    client = genai.Client(
        api_key=api_key
    )

    # ----------------------------------------------
    # BANK DATA
    # ----------------------------------------------

    bank_data = {
        "bank_id":
            bank_row.get("bank_id"),

        "vendor":
            bank_row.get("bank_vendor"),

        "amount":
            bank_row.get("bank_amount"),

        "date":
            str(bank_row.get("bank_date"))
    }

    # ----------------------------------------------
    # INVOICE DATA
    # ----------------------------------------------

    invoice_data = None

    if invoice is not None:

        invoice_data = {
            "invoice_id":
                invoice.get("invoice_id"),

            "vendor":
                invoice.get("vendor"),

            "amount":
                invoice.get("amount"),

            "date":
                str(invoice.get("date"))
        }

    # ----------------------------------------------
    # PROMPT
    # ----------------------------------------------

    prompt = f"""
You are an AI Finance Controller investigating
a difficult bank-to-invoice reconciliation case.

A deterministic reconciliation engine has already
searched for the best candidate invoice, but the
transaction was not considered safe enough for
automatic reconciliation.

Your job is to investigate the evidence and assist
a human finance controller.

BANK TRANSACTION:
{json.dumps(bank_data, indent=2)}

BEST CANDIDATE INVOICE:
{json.dumps(invoice_data, indent=2)}

RULE ENGINE SCORE:
{score}

CONFIDENCE MARGIN OVER SECOND-BEST CANDIDATE:
{margin}

Analyze the case carefully.

Determine:

1. Is the candidate invoice plausible?

2. What discrepancy exists?

3. Identify the most likely exception type.

Possible exception types:

- PARTIAL_PAYMENT
- AMOUNT_MISMATCH
- DATE_MISMATCH
- DUPLICATE_PAYMENT
- MISSING_INVOICE
- VENDOR_MISMATCH
- AMBIGUOUS_MATCH
- OTHER

4. Explain the evidence supporting your conclusion.

5. Recommend what a finance controller should do next.

6. Assess the financial risk.

IMPORTANT:

Do NOT blindly approve a transaction.

If the evidence is insufficient, recommend REVIEW.

Return ONLY valid JSON.

Use exactly this structure:

{{
    "recommendation": "APPROVE | REVIEW | REJECT",
    "reason": "short explanation",
    "exception_type": "type of discrepancy",
    "recommended_action": "specific finance action",
    "risk": "LOW | MEDIUM | HIGH"
}}
"""

    # ----------------------------------------------
    # CALL GEMINI
    # ----------------------------------------------

    try:

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

        text = response.text.strip()

        # ------------------------------------------
        # CLEAN MARKDOWN CODE BLOCKS
        # ------------------------------------------

        if text.startswith("```"):

            text = text.replace(
                "```json",
                ""
            )

            text = text.replace(
                "```",
                ""
            )

            text = text.strip()

        # ------------------------------------------
        # PARSE JSON
        # ------------------------------------------

        result = json.loads(text)

        return result

    except Exception as e:

        print(
            "\n========== GEMINI ERROR =========="
        )

        print(
            type(e).__name__
        )

        print(
            str(e)
        )

        print(
            "==================================\n"
        )

        return {
            "recommendation": "REVIEW",

            "reason":
                f"Gemini review failed: {str(e)}",

            "exception_type":
                "AI_ERROR",

            "recommended_action":
                "Human finance review required.",

            "risk":
                "HIGH"
        }


# ==================================================
# FIND CANDIDATE INVOICES
# ==================================================

def find_candidate_invoices(
    row,
    invoices
):

    bank_vendor = str(
        row["bank_vendor"]
    ).lower()

    if not bank_vendor:

        return invoices.iloc[0:0]

    # First word of vendor name
    vendor_keyword = (
        bank_vendor.split()[0]
    )

    candidates = invoices[
        invoices["vendor"]
        .astype(str)
        .str.lower()
        .str.contains(
            vendor_keyword,
            na=False
        )
    ]

    return candidates


# ==================================================
# CLASSIFY EXCEPTION
# ==================================================

def classify_exception(
    row,
    invoices
):

    """
    Determine WHY a transaction could not
    be safely auto-reconciled.

    Gemini is used only for genuinely ambiguous
    HUMAN_REVIEW cases.
    """

    bank_vendor = str(
        row["bank_vendor"]
    ).lower()

    bank_amount = float(
        row["bank_amount"]
    )

    # ----------------------------------------------
    # FIND CANDIDATES
    # ----------------------------------------------

    candidates = find_candidate_invoices(
        row,
        invoices
    )

    # ----------------------------------------------
    # NO CANDIDATE
    # ----------------------------------------------

    if len(candidates) == 0:

        return {
            "exception_type":
                "MISSING_INVOICE",

            "severity":
                "HIGH",

            "reason":
                "No sufficiently similar invoice was found.",

            "recommended_action":
                "Verify whether the invoice exists outside the reconciliation system.",

            "ai_used":
                False
        }

    # ----------------------------------------------
    # USE BEST CANDIDATE
    # ----------------------------------------------

    candidate = candidates.iloc[0]

    invoice_amount = float(
        candidate["amount"]
    )

    amount_difference = abs(
        bank_amount - invoice_amount
    )

    percentage_difference = (
        amount_difference /
        invoice_amount
        if invoice_amount != 0
        else 1
    )

    # ----------------------------------------------
    # PARTIAL PAYMENT
    # ----------------------------------------------

    if (
        0.15 <= percentage_difference <= 0.60
        and bank_amount < invoice_amount
    ):

        return {
            "exception_type":
                "PARTIAL_PAYMENT",

            "severity":
                "MEDIUM",

            "reason":
                (
                    f"Bank payment is "
                    f"{bank_amount:.2f}, while invoice "
                    f"value is {invoice_amount:.2f}."
                ),

            "recommended_action":
                (
                    "Check whether the remaining invoice "
                    "balance is still outstanding."
                ),

            "ai_used":
                False
        }

    # ----------------------------------------------
    # AMOUNT MISMATCH
    # ----------------------------------------------

    if percentage_difference > 0.05:

        return {
            "exception_type":
                "AMOUNT_MISMATCH",

            "severity":
                "HIGH",

            "reason":
                (
                    f"Payment differs from invoice by "
                    f"{amount_difference:.2f}."
                ),

            "recommended_action":
                (
                    "Verify invoice amount, payment amount "
                    "and possible fees or adjustments."
                ),

            "ai_used":
                False
        }

    # ----------------------------------------------
    # DUPLICATE
    # ----------------------------------------------

    if "-DUP" in str(
        row["bank_id"]
    ):

        return {
            "exception_type":
                "DUPLICATE_PAYMENT",

            "severity":
                "HIGH",

            "reason":
                (
                    "Transaction identifier indicates "
                    "a possible duplicate payment."
                ),

            "recommended_action":
                (
                    "Check whether the original payment "
                    "was already settled."
                ),

            "ai_used":
                False
        }

    # ----------------------------------------------
    # DATE MISMATCH
    # ----------------------------------------------

    try:

        bank_date = pd.to_datetime(
            row["bank_date"]
        )

        invoice_date = pd.to_datetime(
            candidate["date"]
        )

        date_difference = abs(
            (
                bank_date -
                invoice_date
            ).days
        )

        if date_difference > 5:

            return {
                "exception_type":
                    "DATE_MISMATCH",

                "severity":
                    "LOW",

                "reason":
                    (
                        f"Bank and invoice dates differ "
                        f"by {date_difference} days."
                    ),

                "recommended_action":
                    (
                        "Check settlement date versus "
                        "invoice/document date."
                    ),

                "ai_used":
                    False
            }

    except Exception:

        pass

    # ==================================================
    # AMBIGUOUS CASE → GEMINI
    # ==================================================

    print(
        f"AI investigation: "
        f"{row['bank_id']}"
    )

    score = float(
        row.get(
            "confidence",
            0
        )
    )

    margin = float(
        row.get(
            "margin",
            0
        )
    )

    ai_review = ask_gemini_to_review(
        row,
        candidate,
        score,
        margin
    )

    # ----------------------------------------------
    # RETURN AI RESULT
    # ----------------------------------------------

    return {

        "exception_type":
            ai_review.get(
                "exception_type",
                "AMBIGUOUS_MATCH"
            ),

        "severity":
            ai_review.get(
                "risk",
                "MEDIUM"
            ),

        "reason":
            ai_review.get(
                "reason",
                "AI investigation completed."
            ),

        "recommended_action":
            ai_review.get(
                "recommended_action",
                "Human finance review required."
            ),

        "ai_recommendation":
            ai_review.get(
                "recommendation",
                "REVIEW"
            ),

        "ai_used":
            True
    }


# ==================================================
# MAIN
# ==================================================

def main():

    print(
        "Loading reconciliation results..."
    )

    results, invoices = load_data()

    print(
        f"Reconciliation records: "
        f"{len(results)}"
    )

    print(
        f"Invoice records: "
        f"{len(invoices)}"
    )

    # ----------------------------------------------
    # EXCEPTION RESULTS
    # ----------------------------------------------

    exception_results = []

    ai_count = 0

    # ----------------------------------------------
    # PROCESS RECORDS
    # ----------------------------------------------

    for _, row in results.iterrows():

        status = row["status"]

        # Only investigate exceptions
        if status not in [
            "HUMAN_REVIEW",
            "UNRESOLVED"
        ]:

            continue

        classification = classify_exception(
            row,
            invoices
        )

        if classification.get(
            "ai_used",
            False
        ):

            ai_count += 1

        exception_results.append({

            "bank_id":
                row["bank_id"],

            "bank_vendor":
                row["bank_vendor"],

            "bank_amount":
                row["bank_amount"],

            "bank_date":
                row["bank_date"],

            "matched_invoice":
                row.get(
                    "matched_invoice"
                ),

            "confidence":
                row.get(
                    "confidence"
                ),

            "margin":
                row.get(
                    "margin"
                ),

            "exception_type":
                classification.get(
                    "exception_type"
                ),

            "severity":
                classification.get(
                    "severity"
                ),

            "reason":
                classification.get(
                    "reason"
                ),

            "recommended_action":
                classification.get(
                    "recommended_action"
                ),

            "ai_recommendation":
                classification.get(
                    "ai_recommendation",
                    None
                ),

            "ai_used":
                classification.get(
                    "ai_used",
                    False
                )
        })

    # ----------------------------------------------
    # CREATE DATAFRAME
    # ----------------------------------------------

    exception_df = pd.DataFrame(
        exception_results
    )

    # ----------------------------------------------
    # SAVE REPORT
    # ----------------------------------------------

    output_file = (
        DATA_DIR /
        "exception_report.csv"
    )

    exception_df.to_csv(
        output_file,
        index=False
    )

    # ==================================================
    # REPORT
    # ==================================================

    print(
        "\n=============================="
    )

    print(
        "EXCEPTION REPORT"
    )

    print(
        "=============================="
    )

    if len(exception_df) > 0:

        print(
            exception_df[
                "exception_type"
            ].value_counts()
        )

        print(
            "\nSeverity breakdown:"
        )

        print(
            exception_df[
                "severity"
            ].value_counts()
        )

    print(
        f"\nExceptions requiring review: "
        f"{len(exception_df)}"
    )

    print(
        f"AI investigations performed: "
        f"{ai_count}"
    )

    print(
        f"\nSaved:"
        f"\n{output_file}"
    )


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":

    main()