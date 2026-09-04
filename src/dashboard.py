import os
import json
from pathlib import Path

import pandas as pd
import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Finance Controller",
    page_icon="💰",
    layout="wide"
)


# ============================================================
# PATHS
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"

EVALUATED_FILE = DATA_DIR / "evaluated_results.csv"
RECONCILIATION_FILE = DATA_DIR / "reconciliation_results.csv"


# ============================================================
# PAGE STYLE
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 0px;
    }

    .subtitle {
        font-size: 18px;
        color: #666;
        margin-bottom: 30px;
    }

    .section-title {
        font-size: 26px;
        font-weight: 650;
        margin-top: 25px;
    }

    .decision-box {
        padding: 20px;
        border-radius: 10px;
        margin-top: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">💰 AI Finance Controller</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Automated bank-to-invoice reconciliation with '
    'evidence-based exception handling'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_results():

    if not EVALUATED_FILE.exists():

        st.error(
            "evaluated_results.csv was not found."
        )

        st.info(
            "Run the evaluator first:"
            "\n\n"
            "`python src/evaluator.py`"
        )

        st.stop()

    results = pd.read_csv(
        EVALUATED_FILE
    )

    return results


results = load_results()


# ============================================================
# NORMALIZE COLUMN NAMES
# ============================================================

results.columns = [
    str(column).strip()
    for column in results.columns
]


# ============================================================
# BASIC DATA CLEANING
# ============================================================

if "status" in results.columns:

    results["status"] = (
        results["status"]
        .astype(str)
        .str.upper()
        .str.strip()
    )


# ============================================================
# CALCULATE PERFORMANCE METRICS
# ============================================================

total_records = len(results)

auto_matches = results[
    results["status"] == "AUTO_MATCH"
]

human_reviews = results[
    results["status"] == "HUMAN_REVIEW"
]

unresolved = results[
    results["status"] == "UNRESOLVED"
]


auto_count = len(auto_matches)
human_count = len(human_reviews)
unresolved_count = len(unresolved)


# ------------------------------------------------------------
# Automation rate
# ------------------------------------------------------------

if total_records > 0:

    automation_rate = (
        auto_count /
        total_records
    ) * 100

else:

    automation_rate = 0


# ------------------------------------------------------------
# Auto-match precision
# ------------------------------------------------------------

if (
    len(auto_matches) > 0
    and "correct" in auto_matches.columns
):

    auto_match_precision = (
        auto_matches["correct"].mean()
    ) * 100

else:

    auto_match_precision = 0


# ------------------------------------------------------------
# Overall accuracy
# ------------------------------------------------------------

if "correct" in results.columns:

    overall_accuracy = (
        results["correct"].mean()
    ) * 100

else:

    overall_accuracy = 0


# ------------------------------------------------------------
# Average confidence
# ------------------------------------------------------------

if "confidence" in results.columns:

    average_confidence = (
        pd.to_numeric(
            results["confidence"],
            errors="coerce"
        )
        .mean()
    )

else:

    average_confidence = 0


# ============================================================
# KPI SECTION
# ============================================================

st.markdown(
    '<div class="section-title">Controller Performance</div>',
    unsafe_allow_html=True
)

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Records Processed",
        f"{total_records:,}"
    )


with col2:

    st.metric(
        "Automation Rate",
        f"{automation_rate:.2f}%"
    )


with col3:

    st.metric(
        "Auto-Match Precision",
        f"{auto_match_precision:.2f}%"
    )


with col4:

    st.metric(
        "Overall Accuracy",
        f"{overall_accuracy:.2f}%"
    )


# ============================================================
# SECOND KPI ROW
# ============================================================

st.write("")

col5, col6, col7 = st.columns(3)


with col5:

    st.metric(
        "Average Confidence",
        f"{average_confidence:.2f}%"
    )


with col6:

    st.metric(
        "Human Review",
        f"{human_count}"
    )


with col7:

    st.metric(
        "Unresolved",
        f"{unresolved_count}"
    )


# ============================================================
# BENCHMARK SUMMARY
# ============================================================

st.divider()

st.markdown(
    '<div class="section-title">Benchmark Summary</div>',
    unsafe_allow_html=True
)

summary_col1, summary_col2 = st.columns(2)


with summary_col1:

    st.write(
        f"""
        **Dataset**

        - Records processed: **{total_records}**
        - Automatically matched: **{auto_count}**
        - Human review: **{human_count}**
        - Unresolved: **{unresolved_count}**
        """
    )


with summary_col2:

    st.write(
        f"""
        **Measured performance**

        - Automation rate: **{automation_rate:.2f}%**
        - Auto-match precision: **{auto_match_precision:.2f}%**
        - Overall accuracy: **{overall_accuracy:.2f}%**
        - Average confidence: **{average_confidence:.2f}%**
        """
    )


# ============================================================
# EXCEPTION BREAKDOWN
# ============================================================

st.divider()

st.markdown(
    '<div class="section-title">Exception Breakdown</div>',
    unsafe_allow_html=True
)


# Find the most likely exception column

exception_column = None

for column in [
    "exception_type",
    "exception",
    "reason",
    "error_type"
]:

    if column in results.columns:

        exception_column = column
        break


if exception_column is not None:

    exception_counts = (
        results[
            results["status"] != "AUTO_MATCH"
        ][exception_column]
        .fillna("UNKNOWN")
        .astype(str)
        .value_counts()
    )

    if len(exception_counts) > 0:

        st.bar_chart(
            exception_counts
        )

        st.dataframe(
            exception_counts
            .rename("count")
            .reset_index()
            .rename(
                columns={
                    "index": "exception_type"
                }
            ),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.success(
            "No exceptions detected."
        )

else:

    st.info(
        "No exception-type column was found "
        "in evaluated_results.csv."
    )


# ============================================================
# EXCEPTION SEVERITY
# ============================================================

severity_column = None

for column in [
    "severity",
    "risk",
    "risk_level"
]:

    if column in results.columns:

        severity_column = column
        break


if severity_column is not None:

    st.markdown(
        '<div class="section-title">'
        'Exception Severity'
        '</div>',
        unsafe_allow_html=True
    )

    exception_rows = results[
        results["status"] != "AUTO_MATCH"
    ]

    severity_counts = (
        exception_rows[
            severity_column
        ]
        .fillna("UNKNOWN")
        .astype(str)
        .str.upper()
        .value_counts()
    )

    st.dataframe(
        severity_counts
        .rename("count")
        .reset_index()
        .rename(
            columns={
                "index": "severity"
            }
        ),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# TRANSACTION INVESTIGATION
# ============================================================

st.divider()

st.markdown(
    '<div class="section-title">'
    '🔎 Investigate Transaction'
    '</div>',
    unsafe_allow_html=True
)

st.write(
    "Select any transaction to inspect the evidence "
    "behind the controller's decision."
)


# ============================================================
# TRANSACTION SELECTOR
# ============================================================

if "bank_id" in results.columns:

    transaction_ids = (
        results["bank_id"]
        .astype(str)
        .tolist()
    )

    selected_id = st.selectbox(
        "Select transaction",
        transaction_ids
    )

    selected = results[
        results["bank_id"].astype(str)
        == str(selected_id)
    ].iloc[0]

else:

    selected_index = st.selectbox(
        "Select transaction",
        results.index
    )

    selected = results.loc[
        selected_index
    ]


# ============================================================
# TRANSACTION OVERVIEW
# ============================================================

st.markdown(
    "### Transaction Overview"
)

overview_col1, overview_col2, overview_col3 = st.columns(3)


with overview_col1:

    st.write(
        "**Bank ID**"
    )

    st.write(
        selected.get(
            "bank_id",
            "N/A"
        )
    )


with overview_col2:

    st.write(
        "**Vendor**"
    )

    st.write(
        selected.get(
            "bank_vendor",
            selected.get(
                "vendor",
                "N/A"
            )
        )
    )


with overview_col3:

    st.write(
        "**Bank Date**"
    )

    st.write(
        selected.get(
            "bank_date",
            selected.get(
                "date",
                "N/A"
            )
        )
    )


# ============================================================
# DECISION
# ============================================================

status = str(
    selected.get(
        "status",
        "UNKNOWN"
    )
).upper()


st.markdown(
    "### Controller Decision"
)


if status == "AUTO_MATCH":

    st.success(
        "✓ AUTO-MATCH — transaction passed "
        "the deterministic control thresholds."
    )

elif status == "HUMAN_REVIEW":

    st.warning(
        "⚠ HUMAN REVIEW — evidence is plausible "
        "but insufficient for automatic resolution."
    )

elif status == "UNRESOLVED":

    st.error(
        "✕ UNRESOLVED — the controller could not "
        "establish a sufficiently reliable match."
    )

else:

    st.info(
        f"Decision: {status}"
    )


# ============================================================
# DECISION METRICS
# ============================================================

decision_col1, decision_col2, decision_col3 = st.columns(3)


with decision_col1:

    confidence = pd.to_numeric(
        pd.Series(
            [selected.get("confidence")]
        ),
        errors="coerce"
    ).iloc[0]

    if pd.notna(confidence):

        st.metric(
            "Confidence",
            f"{confidence:.2f}%"
        )

    else:

        st.metric(
            "Confidence",
            "N/A"
        )


with decision_col2:

    margin = pd.to_numeric(
        pd.Series(
            [selected.get("margin")]
        ),
        errors="coerce"
    ).iloc[0]

    if pd.notna(margin):

        st.metric(
            "Confidence Margin",
            f"{margin:.2f}"
        )

    else:

        st.metric(
            "Confidence Margin",
            "N/A"
        )


with decision_col3:

    matched_invoice = selected.get(
        "matched_invoice",
        None
    )

    if pd.isna(matched_invoice):

        matched_invoice = "None"

    st.metric(
        "Matched Invoice",
        str(matched_invoice)
    )


# ============================================================
# MATCH EVIDENCE
# ============================================================

st.markdown(
    "### 🔍 Match Evidence"
)


evidence_col1, evidence_col2, evidence_col3 = st.columns(3)


# ------------------------------------------------------------
# Bank amount
# ------------------------------------------------------------

with evidence_col1:

    bank_amount = selected.get(
        "bank_amount",
        None
    )

    try:

        st.metric(
            "Bank Amount",
            f"₹{float(bank_amount):,.2f}"
        )

    except:

        st.metric(
            "Bank Amount",
            "N/A"
        )


# ------------------------------------------------------------
# Invoice amount
# ------------------------------------------------------------

with evidence_col2:

    invoice_amount = selected.get(
        "invoice_amount",
        None
    )

    try:

        st.metric(
            "Invoice Amount",
            f"₹{float(invoice_amount):,.2f}"
        )

    except:

        st.metric(
            "Invoice Amount",
            "N/A"
        )


# ------------------------------------------------------------
# Amount difference
# ------------------------------------------------------------

with evidence_col3:

    amount_difference = selected.get(
        "amount_difference",
        None
    )

    try:

        st.metric(
            "Amount Difference",
            f"₹{float(amount_difference):,.2f}"
        )

    except:

        st.metric(
            "Amount Difference",
            "N/A"
        )


# ============================================================
# DATE EVIDENCE
# ============================================================

date_difference = selected.get(
    "date_difference_days",
    None
)

try:

    date_difference = float(
        date_difference
    )

    st.write(
        f"**Settlement date difference:** "
        f"{date_difference:.0f} day(s)"
    )

except:

    st.write(
        "**Settlement date difference:** N/A"
    )


# ============================================================
# MATCH EVIDENCE TABLE
# ============================================================

evidence_fields = {

    "Bank Vendor":
        selected.get(
            "bank_vendor",
            "N/A"
        ),

    "Matched Invoice":
        selected.get(
            "matched_invoice",
            "N/A"
        ),

    "Bank Amount":
        selected.get(
            "bank_amount",
            "N/A"
        ),

    "Invoice Amount":
        selected.get(
            "invoice_amount",
            "N/A"
        ),

    "Amount Difference":
        selected.get(
            "amount_difference",
            "N/A"
        ),

    "Date Difference":
        selected.get(
            "date_difference_days",
            "N/A"
        ),

    "Confidence":
        selected.get(
            "confidence",
            "N/A"
        ),

    "Confidence Margin":
        selected.get(
            "margin",
            "N/A"
        ),

    "Status":
        status
}


evidence_df = pd.DataFrame(
    list(
        evidence_fields.items()
    ),
    columns=[
        "Evidence",
        "Value"
    ]
)


with st.expander(
    "View detailed evidence"
):

    st.dataframe(
        evidence_df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# EXISTING EXCEPTION INFORMATION
# ============================================================

if status != "AUTO_MATCH":

    st.markdown(
        "### ⚠ Exception Details"
    )

    exception_info = {}

    for column in [
        "exception_type",
        "exception",
        "reason",
        "severity",
        "recommended_action",
        "ai_reason",
        "ai_action",
        "ai_recommendation",
        "ai_risk"
    ]:

        if column in results.columns:

            value = selected.get(
                column
            )

            if pd.notna(value):

                exception_info[
                    column.replace(
                        "_",
                        " "
                    ).title()
                ] = value


    if exception_info:

        for key, value in exception_info.items():

            st.write(
                f"**{key}:** {value}"
            )

    else:

        st.info(
            "No additional exception metadata "
            "is available for this transaction."
        )


# ============================================================
# CLAUDE AI REVIEW
# ============================================================

if status in [
    "HUMAN_REVIEW",
    "UNRESOLVED"
]:

    st.divider()

    st.markdown(
        "### 🤖 AI Finance Controller Review"
    )

    st.write(
        "This transaction is outside the safe "
        "automatic-matching boundary. Claude can "
        "analyze the evidence and recommend the "
        "next finance action."
    )


    # --------------------------------------------------------
    # Check API key
    # --------------------------------------------------------

    api_key_available = bool(
        os.getenv(
            "ANTHROPIC_API_KEY"
        )
    )


    if not api_key_available:

        st.info(
            "Claude review is not configured yet. "
            "Set the ANTHROPIC_API_KEY environment "
            "variable to enable it."
        )

    else:

        review_button = st.button(
            "🤖 Ask Claude to Investigate",
            type="primary"
        )


        if review_button:

            try:

                from exception_classifier import (
                    ask_claude_to_review
                )

                # ----------------------------------------
                # Build bank row
                # ----------------------------------------

                bank_row = {
                    "bank_id":
                        selected.get(
                            "bank_id"
                        ),

                    "vendor":
                        selected.get(
                            "bank_vendor"
                        ),

                    "amount":
                        selected.get(
                            "bank_amount"
                        ),

                    "date":
                        selected.get(
                            "bank_date"
                        )
                }


                # ----------------------------------------
                # Build invoice candidate
                # ----------------------------------------

                invoice = None

                if pd.notna(
                    selected.get(
                        "matched_invoice",
                        None
                    )
                ):

                    invoice = {
                        "invoice_id":
                            selected.get(
                                "matched_invoice"
                            ),

                        "vendor":
                            selected.get(
                                "invoice_vendor",
                                selected.get(
                                    "bank_vendor"
                                )
                            ),

                        "amount":
                            selected.get(
                                "invoice_amount"
                            ),

                        "date":
                            selected.get(
                                "invoice_date"
                            )
                    }


                # ----------------------------------------
                # Score
                # ----------------------------------------

                score = float(
                    selected.get(
                        "confidence",
                        0
                    )
                )


                margin = float(
                    selected.get(
                        "margin",
                        0
                    )
                )


                # ----------------------------------------
                # Call Claude
                # ----------------------------------------

                with st.spinner(
                    "Claude is investigating the transaction..."
                ):

                    ai_result = (
                        ask_claude_to_review(
                            bank_row,
                            invoice,
                            score,
                            margin
                        )
                    )


                # ----------------------------------------
                # Display result
                # ----------------------------------------

                if isinstance(
                    ai_result,
                    dict
                ):

                    ai_col1, ai_col2 = st.columns(2)


                    with ai_col1:

                        recommendation = ai_result.get(
                            "recommendation",
                            "REVIEW"
                        )

                        st.metric(
                            "AI Recommendation",
                            recommendation
                        )


                    with ai_col2:

                        risk = ai_result.get(
                            "risk",
                            "UNKNOWN"
                        )

                        st.metric(
                            "AI Risk",
                            risk
                        )


                    st.write(
                        "**Exception identified**"
                    )

                    st.info(
                        ai_result.get(
                            "exception_type",
                            "Not specified"
                        )
                    )


                    st.write(
                        "**AI Explanation**"
                    )

                    st.write(
                        ai_result.get(
                            "reason",
                            "No explanation returned."
                        )
                    )


                    st.write(
                        "**Recommended Finance Action**"
                    )

                    st.success(
                        ai_result.get(
                            "recommended_action",
                            "Human review required."
                        )
                    )


                    # Store result visually in session
                    st.session_state[
                        "last_ai_result"
                    ] = ai_result


                else:

                    st.warning(
                        "Claude returned an unexpected response."
                    )


            except ImportError:

                st.error(
                    "Could not import "
                    "ask_claude_to_review() from "
                    "exception_classifier.py."
                )

                st.code(
                    "from exception_classifier import "
                    "ask_claude_to_review"
                )


            except Exception as error:

                st.error(
                    "Claude review failed."
                )

                st.code(
                    str(error)
                )


# ============================================================
# ALL TRANSACTIONS
# ============================================================

st.divider()

st.markdown(
    '<div class="section-title">'
    'All Transactions'
    '</div>',
    unsafe_allow_html=True
)


display_columns = [
    column
    for column in [
        "bank_id",
        "bank_vendor",
        "bank_amount",
        "matched_invoice",
        "invoice_amount",
        "amount_difference",
        "date_difference_days",
        "confidence",
        "margin",
        "status",
        "correct"
    ]
    if column in results.columns
]


st.dataframe(
    results[display_columns],
    use_container_width=True,
    hide_index=True
)


# ============================================================
# DOWNLOAD RESULTS
# ============================================================

st.divider()

st.markdown(
    "### Export"
)

csv_data = results.to_csv(
    index=False
).encode("utf-8")


st.download_button(
    label="⬇ Download evaluated results",
    data=csv_data,
    file_name="evaluated_results.csv",
    mime="text/csv"
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "AI Finance Controller • "
    "Deterministic reconciliation + "
    "selective AI investigation"
)