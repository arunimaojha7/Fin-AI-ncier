import pandas as pd
import random
from pathlib import Path

random.seed(42)

# --------------------------------------------------
# PATHS
# --------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


# --------------------------------------------------
# LOAD CLEAN DATA
# --------------------------------------------------

def load_data():

    invoices = pd.read_csv(DATA_DIR / "invoices.csv")
    bank = pd.read_csv(DATA_DIR / "bank_transactions.csv")

    return invoices, bank


# --------------------------------------------------
# VENDOR NAME VARIATIONS
# --------------------------------------------------

VENDOR_VARIATIONS = {
    "Amazon Web Services": "Amazon AWS",
    "Google": "Google India",
    "Microsoft": "Microsoft Corp",
    "Meta Platforms": "Meta",
    "Adobe": "Adobe Systems",
    "IBM": "IBM India",
    "Oracle": "Oracle Corp",
    "Deloitte": "Deloitte India",
    "Accenture": "Accenture Pvt Ltd",
    "Infosys": "Infosys Ltd",
    "Tata Consultancy Services": "TCS",
    "Wipro": "Wipro Ltd",
    "HDFC Bank": "HDFC",
    "ICICI Bank": "ICICI",
    "Axis Bank": "Axis",
}


# --------------------------------------------------
# APPLY VENDOR NOISE
# --------------------------------------------------

def corrupt_vendor(bank, indices):

    for idx in indices:

        original_vendor = bank.loc[idx, "vendor"]

        if original_vendor in VENDOR_VARIATIONS:

            bank.loc[idx, "vendor"] = VENDOR_VARIATIONS[
                original_vendor
            ]

    return bank


# --------------------------------------------------
# APPLY AMOUNT ERRORS
# --------------------------------------------------

def corrupt_amount(bank, indices):

    for idx in indices:

        original_amount = bank.loc[idx, "amount"]

        # Small realistic difference
        adjustment = round(
            original_amount * random.uniform(0.01, 0.05),
            2
        )

        bank.loc[idx, "amount"] = round(
            original_amount + adjustment,
            2
        )

    return bank


# --------------------------------------------------
# APPLY DATE ERRORS
# --------------------------------------------------

def corrupt_date(bank, indices):

    for idx in indices:

        original_date = pd.to_datetime(
            bank.loc[idx, "date"]
        )

        # Settlement can happen a few days later
        days_later = random.randint(1, 5)

        bank.loc[idx, "date"] = (
            original_date +
            pd.Timedelta(days=days_later)
        ).strftime("%Y-%m-%d")

    return bank


# --------------------------------------------------
# CREATE DUPLICATES
# --------------------------------------------------

def create_duplicates(bank, indices):

    duplicates = []

    for idx in indices:

        duplicate = bank.loc[idx].copy()

        duplicate["bank_id"] = (
            duplicate["bank_id"] + "-DUP"
        )

        duplicates.append(duplicate)

    duplicate_df = pd.DataFrame(duplicates)

    bank = pd.concat(
        [bank, duplicate_df],
        ignore_index=True
    )

    return bank


# --------------------------------------------------
# CREATE MISSING INVOICES
# --------------------------------------------------

def remove_invoices(invoices, indices):

    invoices = invoices.drop(
        index=indices
    )

    return invoices.reset_index(drop=True)


# --------------------------------------------------
# CREATE PARTIAL PAYMENTS
# --------------------------------------------------

def create_partial_payments(bank, indices):

    for idx in indices:

        original_amount = bank.loc[idx, "amount"]

        # Pay between 40% and 80% of invoice
        payment_ratio = random.uniform(0.4, 0.8)

        bank.loc[idx, "amount"] = round(
            original_amount * payment_ratio,
            2
        )

    return bank


# --------------------------------------------------
# ADD AMBIGUOUS CASES
# --------------------------------------------------

def create_ambiguous_cases(bank, indices):

    for idx in indices:

        original_vendor = bank.loc[idx, "vendor"]

        # Replace vendor with a deliberately vague name
        if original_vendor == "Amazon Web Services":
            bank.loc[idx, "vendor"] = "Amazon"

        elif original_vendor == "Microsoft":
            bank.loc[idx, "vendor"] = "MS"

        elif original_vendor == "Google":
            bank.loc[idx, "vendor"] = "Google Services"

        else:
            bank.loc[idx, "vendor"] = (
                original_vendor.split()[0]
            )

    return bank


# --------------------------------------------------
# MAIN CORRUPTION PROCESS
# --------------------------------------------------

def main():

    print("Loading clean financial data...")

    invoices, bank = load_data()

    original_count = len(bank)

    print(f"Original bank records: {original_count}")


    # --------------------------------------------------
    # SELECT RECORDS
    # --------------------------------------------------

    all_indices = list(range(original_count))

    random.shuffle(all_indices)

    vendor_indices = all_indices[0:10]

    amount_indices = all_indices[10:18]

    date_indices = all_indices[18:26]

    duplicate_indices = all_indices[26:30]

    missing_invoice_indices = all_indices[30:35]

    partial_indices = all_indices[35:40]

    ambiguous_indices = all_indices[40:45]


    # --------------------------------------------------
    # APPLY CORRUPTIONS
    # --------------------------------------------------

    bank = corrupt_vendor(
        bank,
        vendor_indices
    )

    bank = corrupt_amount(
        bank,
        amount_indices
    )

    bank = corrupt_date(
        bank,
        date_indices
    )

    bank = create_partial_payments(
        bank,
        partial_indices
    )

    bank = create_ambiguous_cases(
        bank,
        ambiguous_indices
    )

    bank = create_duplicates(
        bank,
        duplicate_indices
    )

    invoices = remove_invoices(
        invoices,
        missing_invoice_indices
    )


    # --------------------------------------------------
    # SAVE CORRUPTED DATA
    # --------------------------------------------------

    bank.to_csv(
        DATA_DIR / "messy_bank_transactions.csv",
        index=False
    )

    invoices.to_csv(
        DATA_DIR / "messy_invoices.csv",
        index=False
    )


    # --------------------------------------------------
    # CREATE CORRUPTION LOG
    # --------------------------------------------------

    corruption_log = []

    for idx in vendor_indices:
        corruption_log.append({
            "transaction_id":
                f"T{idx + 1:04d}",
            "issue":
                "vendor_variation"
        })

    for idx in amount_indices:
        corruption_log.append({
            "transaction_id":
                f"T{idx + 1:04d}",
            "issue":
                "amount_mismatch"
        })

    for idx in date_indices:
        corruption_log.append({
            "transaction_id":
                f"T{idx + 1:04d}",
            "issue":
                "date_mismatch"
        })

    for idx in duplicate_indices:
        corruption_log.append({
            "transaction_id":
                f"T{idx + 1:04d}",
            "issue":
                "duplicate"
        })

    for idx in missing_invoice_indices:
        corruption_log.append({
            "transaction_id":
                f"T{idx + 1:04d}",
            "issue":
                "missing_invoice"
        })

    for idx in partial_indices:
        corruption_log.append({
            "transaction_id":
                f"T{idx + 1:04d}",
            "issue":
                "partial_payment"
        })

    for idx in ambiguous_indices:
        corruption_log.append({
            "transaction_id":
                f"T{idx + 1:04d}",
            "issue":
                "ambiguous_vendor"
        })


    corruption_log = pd.DataFrame(
        corruption_log
    )

    corruption_log.to_csv(
        DATA_DIR / "corruption_log.csv",
        index=False
    )


    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------

    print("\nCorruption complete!")

    print(
        f"Bank records: {len(bank)}"
    )

    print(
        f"Invoices: {len(invoices)}"
    )

    print("\nProblems introduced:")

    print("Vendor variations: 10")
    print("Amount mismatches: 8")
    print("Date mismatches: 8")
    print("Duplicates: 4")
    print("Missing invoices: 5")
    print("Partial payments: 5")
    print("Ambiguous vendors: 5")


if __name__ == "__main__":
    main()