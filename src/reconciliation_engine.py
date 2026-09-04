import pandas as pd
from rapidfuzz.fuzz import ratio
from pathlib import Path


# --------------------------------------------------
# PATHS
# --------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


# --------------------------------------------------
# SETTINGS
# --------------------------------------------------

AMOUNT_TOLERANCE = 0.02
DATE_TOLERANCE_DAYS = 5

AUTO_MATCH_THRESHOLD = 85
REVIEW_THRESHOLD = 65


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

def load_data():

    bank = pd.read_csv(
        DATA_DIR / "messy_bank_transactions.csv"
    )

    invoices = pd.read_csv(
        DATA_DIR / "messy_invoices.csv"
    )

    return bank, invoices


# --------------------------------------------------
# NORMALIZE VENDOR
# --------------------------------------------------

def normalize_vendor(name):

    if pd.isna(name):
        return ""

    name = str(name).lower()

    replacements = {
        " ltd": "",
        " pvt": "",
        " pvt ltd": "",
        " corp": "",
        " india": "",
        " systems": "",
        " services": "",
    }

    for old, new in replacements.items():
        name = name.replace(old, new)

    name = name.replace(".", "")
    name = name.replace(",", "")
    name = name.strip()

    return name


# --------------------------------------------------
# VENDOR SIMILARITY
# --------------------------------------------------

def vendor_similarity(bank_vendor, invoice_vendor):

    bank_vendor = normalize_vendor(
        bank_vendor
    )

    invoice_vendor = normalize_vendor(
        invoice_vendor
    )

    return ratio(
        bank_vendor,
        invoice_vendor
    )


# --------------------------------------------------
# AMOUNT SCORE
# --------------------------------------------------

def amount_score(bank_amount, invoice_amount):

    if invoice_amount == 0:
        return 0

    difference = abs(
        bank_amount - invoice_amount
    )

    percentage_difference = (
        difference / invoice_amount
    )

    if percentage_difference == 0:
        return 100

    if percentage_difference <= 0.01:
        return 95

    if percentage_difference <= 0.02:
        return 85

    if percentage_difference <= 0.05:
        return 60

    return 0


# --------------------------------------------------
# DATE SCORE
# --------------------------------------------------

def date_score(bank_date, invoice_date):

    bank_date = pd.to_datetime(bank_date)

    invoice_date = pd.to_datetime(invoice_date)

    difference = abs(
        (bank_date - invoice_date).days
    )

    if difference == 0:
        return 100

    if difference <= 2:
        return 90

    if difference <= 5:
        return 75

    if difference <= 10:
        return 40

    return 0


# --------------------------------------------------
# COMBINED SCORE
# --------------------------------------------------

def calculate_score(
    bank_row,
    invoice_row
):

    vendor = vendor_similarity(
        bank_row["vendor"],
        invoice_row["vendor"]
    )

    amount = amount_score(
        bank_row["amount"],
        invoice_row["amount"]
    )

    date = date_score(
        bank_row["date"],
        invoice_row["date"]
    )

    # Weighted score
    final_score = (
        vendor * 0.45
        + amount * 0.40
        + date * 0.15
    )

    return round(final_score, 2)


# --------------------------------------------------
# FIND BEST MATCH
# --------------------------------------------------

def find_best_match(bank_row, invoices):

    candidates = []

    for _, invoice in invoices.iterrows():

        score = calculate_score(
            bank_row,
            invoice
        )

        candidates.append({
            "invoice": invoice,
            "score": score
        })

    # Highest score first
    candidates.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    if not candidates:
        return None, 0, 0

    best = candidates[0]

    best_invoice = best["invoice"]
    best_score = best["score"]

    # Second-best candidate
    if len(candidates) > 1:
        second_score = candidates[1]["score"]
    else:
        second_score = 0

    margin = best_score - second_score

    return (
        best_invoice,
        best_score,
        margin
    )


# --------------------------------------------------
# CLASSIFY RESULT
# --------------------------------------------------

def classify_match(score, margin):

    # Very high confidence but weak separation
    # means the system is unsure.

    if score >= 85 and margin < 5:

        return "HUMAN_REVIEW"

    if score >= 85:

        return "AUTO_MATCH"

    if score >= 65:

        return "HUMAN_REVIEW"

    return "UNRESOLVED"


# --------------------------------------------------
# RECONCILE
# --------------------------------------------------

# --------------------------------------------------
# RECONCILE
# --------------------------------------------------

def reconcile(bank, invoices):

    results = []

    for _, bank_row in bank.iterrows():

        # Find best invoice match
        invoice, score, margin = find_best_match(
            bank_row,
            invoices
        )

        # Decide what to do
        status = classify_match(
            score,
            margin
        )

        # -----------------------------------------
        # MATCHED INVOICE
        # -----------------------------------------

        if invoice is not None:

            invoice_id = invoice["invoice_id"]

            invoice_amount = float(
                invoice["amount"]
            )

            bank_amount = float(
                bank_row["amount"]
            )

            # Amount evidence
            amount_difference = abs(
                bank_amount - invoice_amount
            )

            # Date evidence
            try:

                bank_date = pd.to_datetime(
                    bank_row["date"]
                )

                invoice_date = pd.to_datetime(
                    invoice["date"]
                )

                date_difference = abs(
                    (bank_date - invoice_date).days
                )

            except Exception:

                date_difference = None

        # -----------------------------------------
        # NO MATCH
        # -----------------------------------------

        else:

            invoice_id = None
            invoice_amount = None
            amount_difference = None
            date_difference = None

        # -----------------------------------------
        # SAVE RESULT
        # -----------------------------------------

        results.append({

            "bank_id":
                bank_row["bank_id"],

            "bank_vendor":
                bank_row["vendor"],

            "bank_amount":
                bank_row["amount"],

            "bank_date":
                bank_row["date"],

            "matched_invoice":
                invoice_id,

            "invoice_amount":
                invoice_amount,

            "amount_difference":
                amount_difference,

            "date_difference_days":
                date_difference,

            "confidence":
                score,

            "margin":
                margin,

            "status":
                status

        })

    return pd.DataFrame(results)


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    print("Loading financial data...")

    bank, invoices = load_data()

    print(
        f"Bank records: {len(bank)}"
    )

    print(
        f"Invoices: {len(invoices)}"
    )

    print("\nRunning reconciliation...")

    results = reconcile(
        bank,
        invoices
    )

    output_file = (
        DATA_DIR /
        "reconciliation_results.csv"
    )

    results.to_csv(
        output_file,
        index=False
    )

    print(
        f"\nResults saved to:"
        f"\n{output_file}"
    )

    print("\nRESULT SUMMARY")

    print(
        results["status"]
        .value_counts()
    )

    print("\nAverage confidence:")

    print(
        round(
            results["confidence"].mean(),
            2
        )
    )


if __name__ == "__main__":
    main()