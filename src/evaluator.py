import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_results():
    results = pd.read_csv(
        DATA_DIR / "reconciliation_results.csv"
    )

    ground_truth = pd.read_csv(
        DATA_DIR / "ground_truth.csv"
    )

    corruption_log = pd.read_csv(
        DATA_DIR / "corruption_log.csv"
    )

    return results, ground_truth, corruption_log


def get_transaction_id(invoice_id):
    """
    Convert INV-T0001 -> T0001
    """
    if pd.isna(invoice_id):
        return None

    return str(invoice_id).replace("INV-", "")


def evaluate(results, ground_truth):

    results["predicted_transaction_id"] = (
        results["matched_invoice"]
        .apply(get_transaction_id)
    )

    # --------------------------------------------------
    # Determine the TRUE transaction
    # --------------------------------------------------

    true_mapping = dict(
        zip(
            ground_truth["transaction_id"],
            ground_truth["transaction_id"]
        )
    )

    results["correct"] = (
        results["predicted_transaction_id"]
        == results["bank_id"]
        .str.replace("BANK-", "", regex=False)
        .str.replace("-DUP", "", regex=False)
    )

    return results


def calculate_metrics(results):

    total = len(results)

    auto_matches = results[
        results["status"] == "AUTO_MATCH"
    ]

    human_review = results[
        results["status"] == "HUMAN_REVIEW"
    ]

    unresolved = results[
        results["status"] == "UNRESOLVED"
    ]

    # Accuracy among automatic decisions
    if len(auto_matches) > 0:

        auto_accuracy = (
            auto_matches["correct"].mean() * 100
        )

    else:

        auto_accuracy = 0

    # Overall correctness
    overall_accuracy = (
        results["correct"].mean() * 100
    )

    return {
        "total": total,
        "auto_matches": len(auto_matches),
        "human_review": len(human_review),
        "unresolved": len(unresolved),
        "auto_accuracy": auto_accuracy,
        "overall_accuracy": overall_accuracy
    }


def main():

    print("Loading evaluation data...")

    results, ground_truth, corruption_log = (
        load_results()
    )

    results = evaluate(
        results,
        ground_truth
    )

    metrics = calculate_metrics(
        results
    )

    print("\n==============================")
    print("FINANCE CONTROLLER EVALUATION")
    print("==============================")

    print(
        f"Total records: "
        f"{metrics['total']}"
    )

    print(
        f"Auto matches: "
        f"{metrics['auto_matches']}"
    )

    print(
        f"Human review: "
        f"{metrics['human_review']}"
    )

    print(
        f"Unresolved: "
        f"{metrics['unresolved']}"
    )

    print(
        f"\nAUTO-MATCH ACCURACY: "
        f"{metrics['auto_accuracy']:.2f}%"
    )

    print(
        f"OVERALL ACCURACY: "
        f"{metrics['overall_accuracy']:.2f}%"
    )

    # --------------------------------------------------
    # SHOW WRONG AUTOMATIC MATCHES
    # --------------------------------------------------

    wrong_auto = results[
        (results["status"] == "AUTO_MATCH")
        & (results["correct"] == False)
    ]

    print(
        f"\nWrong automatic matches: "
        f"{len(wrong_auto)}"
    )

    if len(wrong_auto) > 0:

        print("\nExamples:")

        print(
            wrong_auto[
                [
                    "bank_id",
                    "bank_vendor",
                    "bank_amount",
                    "matched_invoice",
                    "confidence"
                ]
            ].head(10).to_string(
                index=False
            )
        )

    # --------------------------------------------------
    # SAVE EVALUATED RESULTS
    # --------------------------------------------------

    results.to_csv(
        DATA_DIR / "evaluated_results.csv",
        index=False
    )

    print(
        "\nSaved:"
        "\ndata/evaluated_results.csv"
    )


if __name__ == "__main__":
    main()