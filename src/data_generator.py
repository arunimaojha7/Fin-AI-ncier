import pandas as pd
import random
from faker import Faker
from datetime import datetime, timedelta
from pathlib import Path

fake = Faker()
random.seed(42)

# -----------------------------
# SETTINGS
# -----------------------------

NUM_RECORDS = 100

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


# -----------------------------
# VENDORS
# -----------------------------

VENDORS = [
    "Amazon Web Services",
    "Google",
    "Microsoft",
    "Meta Platforms",
    "Adobe",
    "IBM",
    "Oracle",
    "Deloitte",
    "Accenture",
    "Infosys",
    "Tata Consultancy Services",
    "Wipro",
    "HDFC Bank",
    "ICICI Bank",
    "Axis Bank",
]


# -----------------------------
# GENERATE BASE TRANSACTIONS
# -----------------------------

def generate_transactions(n):
    transactions = []

    start_date = datetime(2026, 7, 1)

    for i in range(1, n + 1):

        vendor = random.choice(VENDORS)

        amount = round(random.uniform(1000, 100000), 2)

        date = start_date + timedelta(
            days=random.randint(0, 30)
        )

        transaction = {
            "transaction_id": f"T{i:04d}",
            "vendor": vendor,
            "amount": amount,
            "date": date.strftime("%Y-%m-%d"),
            "currency": "INR",
        }

        transactions.append(transaction)

    return pd.DataFrame(transactions)


# -----------------------------
# CREATE INVOICES
# -----------------------------

def create_invoices(transactions):

    invoices = []

    for _, row in transactions.iterrows():

        invoices.append({
            "invoice_id": f"INV-{row['transaction_id']}",
            "vendor": row["vendor"],
            "amount": row["amount"],
            "date": row["date"],
            "currency": row["currency"],
            "transaction_id": row["transaction_id"],
        })

    return pd.DataFrame(invoices)


# -----------------------------
# CREATE BANK RECORDS
# -----------------------------

def create_bank_records(transactions):

    bank_records = []

    for _, row in transactions.iterrows():

        bank_records.append({
            "bank_id": f"BANK-{row['transaction_id']}",
            "vendor": row["vendor"],
            "amount": row["amount"],
            "date": row["date"],
            "currency": row["currency"],
            "transaction_id": row["transaction_id"],
        })

    return pd.DataFrame(bank_records)


# -----------------------------
# CREATE LEDGER RECORDS
# -----------------------------

def create_ledger_records(transactions):

    ledger_records = []

    for _, row in transactions.iterrows():

        ledger_records.append({
            "ledger_id": f"LED-{row['transaction_id']}",
            "vendor": row["vendor"],
            "amount": row["amount"],
            "date": row["date"],
            "currency": row["currency"],
            "transaction_id": row["transaction_id"],
        })

    return pd.DataFrame(ledger_records)


# -----------------------------
# MAIN
# -----------------------------

def main():

    print("Generating synthetic finance data...")

    transactions = generate_transactions(NUM_RECORDS)

    invoices = create_invoices(transactions)

    bank = create_bank_records(transactions)

    ledger = create_ledger_records(transactions)

    # Save files

    transactions.to_csv(
        DATA_DIR / "ground_truth.csv",
        index=False
    )

    invoices.to_csv(
        DATA_DIR / "invoices.csv",
        index=False
    )

    bank.to_csv(
        DATA_DIR / "bank_transactions.csv",
        index=False
    )

    ledger.to_csv(
        DATA_DIR / "ledger.csv",
        index=False
    )

    print(f"Generated {NUM_RECORDS} transactions.")

    print("\nFiles created:")

    print(" - ground_truth.csv")
    print(" - invoices.csv")
    print(" - bank_transactions.csv")
    print(" - ledger.csv")


if __name__ == "__main__":
    main()