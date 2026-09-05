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
    page_icon="◆",
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
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Serif:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">

    <style>

    :root {
        --ink: #1A2332;
        --ink-soft: #4A5568;
        --paper: #FAF9F6;
        --paper-raised: #FFFFFF;
        --line: #DDD8CC;
        --gold: #B8860B;
        --forest: #2D5F4C;
        --forest-bg: #EAF1EC;
        --amber: #96690E;
        --amber-bg: #FBF1DE;
        --brick: #8B3A3A;
        --brick-bg: #F7EBEA;
    }

    /* Base */
    .stApp {
        background-color: var(--paper);
    }

    html, body, [class*="css"]  {
        font-family: 'IBM Plex Sans', sans-serif;
        color: var(--ink);
    }

    h1, h2, h3 {
        font-family: 'IBM Plex Serif', serif !important;
        color: var(--ink) !important;
        font-weight: 600 !important;
    }

    /* Masthead */
    .masthead {
        border-bottom: 2px solid var(--ink);
        padding-bottom: 18px;
        margin-bottom: 6px;
    }

    .masthead-title {
        font-family: 'IBM Plex Serif', serif;
        font-size: 38px;
        font-weight: 700;
        color: var(--ink);
        letter-spacing: -0.5px;
        margin-bottom: 4px;
    }

    .masthead-subtitle {
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 15px;
        color: var(--ink-soft);
    }

    /* Section headers: numbered like statement sections */
    .section-header {
        font-family: 'IBM Plex Serif', serif;
        font-size: 21px;
        font-weight: 600;
        color: var(--ink);
        border-bottom: 1px solid var(--line);
        padding-bottom: 8px;
        margin-top: 8px;
        margin-bottom: 16px;
    }

    /* KPI metric styling */
    div[data-testid="stMetric"] {
        background-color: var(--paper-raised);
        border: 1px solid var(--line);
        border-left: 3px solid var(--ink);
        padding: 14px 16px;
        border-radius: 2px;
    }

    div[data-testid="stMetricLabel"] {
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 12.5px;
        color: var(--ink-soft);
        font-weight: 500;
    }

    div[data-testid="stMetricValue"] {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 26px;
        color: var(--ink);
    }

    /* Status banners — replace default emoji alert boxes with ledger-style bars */
    .decision-banner {
        padding: 14px 18px;
        border-radius: 2px;
        font-size: 15px;
        font-weight: 500;
        margin: 8px 0 18px 0;
        border-left: 4px solid;
    }

    .decision-auto {
        background-color: var(--forest-bg);
        border-color: var(--forest);
        color: var(--forest);
    }

    .decision-review {
        background-color: var(--amber-bg);
        border-color: var(--amber);
        color: var(--amber);
    }

    .decision-unresolved {
        background-color: var(--brick-bg);
        border-color: var(--brick);
        color: var(--brick);
    }

    /* Dataframes */
    div[data-testid="stDataFrame"] {
        border: 1px solid var(--line);
    }

    /* Buttons */
    .stButton button, .stDownloadButton button {
        font-family: 'IBM Plex Sans', sans-serif;
        font-weight: 500;
        border-radius: 2px;
        border: 1px solid var(--ink);
    }

    /* Divider replacement spacing */
    hr {
        border-color: var(--line) !important;
        margin: 28px 0 !important;
    }

    /* Expander */
    div[data-testid="stExpander"] {
        border: 1px solid var(--line);
        border-radius: 2px;
    }

    .field-row {
        display: flex;
        justify-content: space-between;
        padding: 6px 0;
        border-bottom: 1px solid var(--line);
        font-size: 14.5px;
    }

    .field-label {
        color: var(--ink-soft);
    }

    .field-value {
        font-family: 'IBM Plex Mono', monospace;
        color: var(--ink);
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="masthead">
        <div class="masthead-title">AI Finance Controller</div>
        <div class="masthead-subtitle">
            Automated bank-to-invoice reconciliation, with evidence-based
            escalation for exceptions the rule engine cannot safely resolve.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.write("")


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

auto_matches = results[results["status"] == "AUTO_MATCH"]
human_reviews = results[results["status"] == "HUMAN_REVIEW"]
unresolved = results[results["status"] == "UNRESOLVED"]

auto_count = len(auto_matches)
human_count = len(human_reviews)
unresolved_count = len(unresolved)

automation_rate = (
    (auto_count / total_records) * 100
    if total_records > 0 else 0
)

auto_match_precision = (
    (auto_matches["correct"].mean()) * 100
    if len(auto_matches) > 0 and "correct" in auto_matches.columns
    else 0
)

overall_accuracy = (
    (results["correct"].mean()) * 100
    if "correct" in results.columns else 0
)

average_confidence = (
    pd.to_numeric(results["confidence"], errors="coerce").mean()
    if "confidence" in results.columns else 0
)


# ============================================================
# KPI SECTION
# ============================================================

st.markdown(
    '<div class="section-header">01 · Controller Performance</div>',
    unsafe_allow_html=True
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Records Processed", f"{total_records:,}")

with col2:
    st.metric("Automation Rate", f"{automation_rate:.1f}%")

with col3:
    st.metric("Auto-Match Precision", f"{auto_match_precision:.1f}%")

with col4:
    st.metric("Overall Accuracy", f"{overall_accuracy:.1f}%")

st.write("")

col5, col6, col7 = st.columns(3)

with col5:
    st.metric("Average Confidence", f"{average_confidence:.1f}%")

with col6:
    st.metric("Escalated for Review", f"{human_count}")

with col7:
    st.metric("Unresolved", f"{unresolved_count}")


# ============================================================
# BENCHMARK SUMMARY
# ============================================================

st.write("")
st.write("")

st.markdown(
    '<div class="section-header">02 · Benchmark Summary</div>',
    unsafe_allow_html=True
)

summary_col1, summary_col2 = st.columns(2)

with summary_col1:
    st.markdown(
        f"""
        <div class="field-row"><span class="field-label">Records processed</span><span class="field-value">{total_records}</span></div>
        <div class="field-row"><span class="field-label">Automatically matched</span><span class="field-value">{auto_count}</span></div>
        <div class="field-row"><span class="field-label">Escalated for review</span><span class="field-value">{human_count}</span></div>
        <div class="field-row"><span class="field-label">Unresolved</span><span class="field-value">{unresolved_count}</span></div>
        """,
        unsafe_allow_html=True
    )

with summary_col2:
    st.markdown(
        f"""
        <div class="field-row"><span class="field-label">Automation rate</span><span class="field-value">{automation_rate:.2f}%</span></div>
        <div class="field-row"><span class="field-label">Auto-match precision</span><span class="field-value">{auto_match_precision:.2f}%</span></div>
        <div class="field-row"><span class="field-label">Overall accuracy</span><span class="field-value">{overall_accuracy:.2f}%</span></div>
        <div class="field-row"><span class="field-label">Average confidence</span><span class="field-value">{average_confidence:.2f}%</span></div>
        """,
        unsafe_allow_html=True
    )

st.caption(
    f"The rule engine resolved {automation_rate:.0f}% of transactions without "
    f"any AI involvement. AI investigation is reserved for the remaining "
    f"{human_count + unresolved_count} cases the engine could not confidently classify."
)


# ============================================================
# EXCEPTION BREAKDOWN
# ============================================================

st.write("")
st.markdown(
    '<div class="section-header">03 · Exception Breakdown</div>',
    unsafe_allow_html=True
)

exception_column = None

for column in ["exception_type", "exception", "reason", "error_type"]:
    if column in results.columns:
        exception_column = column
        break

if exception_column is not None:

    exception_counts = (
        results[results["status"] != "AUTO_MATCH"][exception_column]
        .fillna("UNKNOWN")
        .astype(str)
        .value_counts()
    )

    if len(exception_counts) > 0:

        chart_col, table_col = st.columns([3, 2])

        with chart_col:
            st.bar_chart(exception_counts, color="#1A2332")

        with table_col:
            st.dataframe(
                exception_counts.rename("count").reset_index()
                .rename(columns={"index": "exception_type"}),
                use_container_width=True,
                hide_index=True
            )

    else:
        st.success("No exceptions detected.")

else:
    st.info("No exception-type column was found in evaluated_results.csv.")


# ============================================================
# EXCEPTION SEVERITY
# ============================================================

severity_column = None

for column in ["severity", "risk", "risk_level"]:
    if column in results.columns:
        severity_column = column
        break

if severity_column is not None:

    st.write("")
    st.markdown(
        '<div class="section-header">04 · Exception Severity</div>',
        unsafe_allow_html=True
    )

    exception_rows = results[results["status"] != "AUTO_MATCH"]

    severity_counts = (
        exception_rows[severity_column]
        .fillna("UNKNOWN")
        .astype(str)
        .str.upper()
        .value_counts()
    )

    st.dataframe(
        severity_counts.rename("count").reset_index()
        .rename(columns={"index": "severity"}),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# TRANSACTION INVESTIGATION
# ============================================================

st.write("")
st.markdown(
    '<div class="section-header">05 · Investigate Transaction</div>',
    unsafe_allow_html=True
)

st.caption(
    "Select any transaction to inspect the evidence behind the controller's decision."
)

if "bank_id" in results.columns:

    transaction_ids = results["bank_id"].astype(str).tolist()

    selected_id = st.selectbox("Select transaction", transaction_ids)

    selected = results[
        results["bank_id"].astype(str) == str(selected_id)
    ].iloc[0]

else:

    selected_index = st.selectbox("Select transaction", results.index)
    selected = results.loc[selected_index]


# ------------------------------------------------------------
# Transaction overview
# ------------------------------------------------------------

st.write("")
overview_col1, overview_col2, overview_col3 = st.columns(3)

with overview_col1:
    st.metric("Bank ID", selected.get("bank_id", "N/A"))

with overview_col2:
    st.metric(
        "Vendor",
        selected.get("bank_vendor", selected.get("vendor", "N/A"))
    )

with overview_col3:
    st.metric(
        "Bank Date",
        selected.get("bank_date", selected.get("date", "N/A"))
    )


# ------------------------------------------------------------
# Decision banner
# ------------------------------------------------------------

status = str(selected.get("status", "UNKNOWN")).upper()

st.write("")

if status == "AUTO_MATCH":
    st.markdown(
        '<div class="decision-banner decision-auto">'
        'AUTO-MATCH — transaction passed the deterministic control thresholds.'
        '</div>',
        unsafe_allow_html=True
    )

elif status == "HUMAN_REVIEW":
    st.markdown(
        '<div class="decision-banner decision-review">'
        'HUMAN REVIEW — evidence is plausible but insufficient for automatic resolution.'
        '</div>',
        unsafe_allow_html=True
    )

elif status == "UNRESOLVED":
    st.markdown(
        '<div class="decision-banner decision-unresolved">'
        'UNRESOLVED — the controller could not establish a sufficiently reliable match.'
        '</div>',
        unsafe_allow_html=True
    )

else:
    st.info(f"Decision: {status}")


# ------------------------------------------------------------
# Decision metrics
# ------------------------------------------------------------

decision_col1, decision_col2, decision_col3 = st.columns(3)

with decision_col1:
    confidence = pd.to_numeric(
        pd.Series([selected.get("confidence")]), errors="coerce"
    ).iloc[0]
    st.metric("Confidence", f"{confidence:.2f}%" if pd.notna(confidence) else "N/A")

with decision_col2:
    margin = pd.to_numeric(
        pd.Series([selected.get("margin")]), errors="coerce"
    ).iloc[0]
    st.metric("Confidence Margin", f"{margin:.2f}" if pd.notna(margin) else "N/A")

with decision_col3:
    matched_invoice = selected.get("matched_invoice", None)
    if pd.isna(matched_invoice):
        matched_invoice = "None"
    st.metric("Matched Invoice", str(matched_invoice))


# ------------------------------------------------------------
# Match evidence
# ------------------------------------------------------------

st.write("")
st.markdown("**Match Evidence**")

evidence_col1, evidence_col2, evidence_col3 = st.columns(3)

with evidence_col1:
    try:
        st.metric("Bank Amount", f"₹{float(selected.get('bank_amount')):,.2f}")
    except Exception:
        st.metric("Bank Amount", "N/A")

with evidence_col2:
    try:
        st.metric("Invoice Amount", f"₹{float(selected.get('invoice_amount')):,.2f}")
    except Exception:
        st.metric("Invoice Amount", "N/A")

with evidence_col3:
    try:
        st.metric("Amount Difference", f"₹{float(selected.get('amount_difference')):,.2f}")
    except Exception:
        st.metric("Amount Difference", "N/A")

try:
    date_difference = float(selected.get("date_difference_days", None))
    st.caption(f"Settlement date difference: {date_difference:.0f} day(s)")
except Exception:
    st.caption("Settlement date difference: N/A")


# ------------------------------------------------------------
# Full evidence table
# ------------------------------------------------------------

evidence_fields = {
    "Bank Vendor": selected.get("bank_vendor", "N/A"),
    "Matched Invoice": selected.get("matched_invoice", "N/A"),
    "Bank Amount": selected.get("bank_amount", "N/A"),
    "Invoice Amount": selected.get("invoice_amount", "N/A"),
    "Amount Difference": selected.get("amount_difference", "N/A"),
    "Date Difference": selected.get("date_difference_days", "N/A"),
    "Confidence": selected.get("confidence", "N/A"),
    "Confidence Margin": selected.get("margin", "N/A"),
    "Status": status
}

evidence_df = pd.DataFrame(
    list(evidence_fields.items()), columns=["Evidence", "Value"]
)

with st.expander("View detailed evidence"):
    st.dataframe(evidence_df, use_container_width=True, hide_index=True)


# ------------------------------------------------------------
# Existing exception info
# ------------------------------------------------------------

if status != "AUTO_MATCH":

    st.write("")
    st.markdown("**Exception Details**")

    exception_info = {}

    for column in [
        "exception_type", "exception", "reason", "severity",
        "recommended_action", "ai_reason", "ai_action",
        "ai_recommendation", "ai_risk"
    ]:
        if column in results.columns:
            value = selected.get(column)
            if pd.notna(value):
                exception_info[column.replace("_", " ").title()] = value

    if exception_info:
        for key, value in exception_info.items():
            st.markdown(
                f'<div class="field-row"><span class="field-label">{key}</span>'
                f'<span class="field-value">{value}</span></div>',
                unsafe_allow_html=True
            )
    else:
        st.caption("No additional exception metadata is available for this transaction.")


# ============================================================
# AI REVIEW (GEMINI)
# ============================================================

if status in ["HUMAN_REVIEW", "UNRESOLVED"]:

    st.write("")
    st.markdown(
        '<div class="section-header">06 · AI Investigation</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "This transaction is outside the safe automatic-matching boundary. "
        "Gemini can analyze the evidence and recommend the next finance action."
    )

    api_key_available = bool(os.getenv("GEMINI_API_KEY"))

    if not api_key_available:

        st.info(
            "AI review is not configured yet. Set the GEMINI_API_KEY "
            "environment variable to enable it."
        )

    else:

        review_button = st.button("Investigate with AI", type="primary")

        if review_button:

            try:

                from exception_classifier import ask_gemini_to_review

                bank_row = {
                    "bank_id": selected.get("bank_id"),
                    "bank_vendor": selected.get("bank_vendor"),
                    "bank_amount": selected.get("bank_amount"),
                    "bank_date": selected.get("bank_date"),
                }

                invoice = None

                if pd.notna(selected.get("matched_invoice", None)):
                    invoice = {
                        "invoice_id": selected.get("matched_invoice"),
                        "vendor": selected.get(
                            "invoice_vendor", selected.get("bank_vendor")
                        ),
                        "amount": selected.get("invoice_amount"),
                        "date": selected.get("invoice_date"),
                    }

                score = float(selected.get("confidence", 0))
                margin = float(selected.get("margin", 0))

                with st.spinner("Gemini is investigating the transaction..."):
                    ai_result = ask_gemini_to_review(
                        bank_row, invoice, score, margin
                    )

                if isinstance(ai_result, dict):

                    ai_col1, ai_col2 = st.columns(2)

                    with ai_col1:
                        st.metric(
                            "AI Recommendation",
                            ai_result.get("recommendation", "REVIEW")
                        )

                    with ai_col2:
                        st.metric("AI Risk", ai_result.get("risk", "UNKNOWN"))

                    st.markdown("**Exception identified**")
                    st.info(ai_result.get("exception_type", "Not specified"))

                    st.markdown("**AI Explanation**")
                    st.write(ai_result.get("reason", "No explanation returned."))

                    st.markdown("**Recommended Finance Action**")
                    st.success(
                        ai_result.get("recommended_action", "Human review required.")
                    )

                    st.session_state["last_ai_result"] = ai_result

                else:
                    st.warning("Gemini returned an unexpected response.")

            except ImportError:
                st.error(
                    "Could not import ask_gemini_to_review() from exception_classifier.py."
                )
                st.code("from exception_classifier import ask_gemini_to_review")

            except Exception as error:
                st.error("AI review failed.")
                st.code(str(error))


# ============================================================
# ALL TRANSACTIONS
# ============================================================

st.write("")
st.markdown(
    '<div class="section-header">07 · All Transactions</div>',
    unsafe_allow_html=True
)

display_columns = [
    column for column in [
        "bank_id", "bank_vendor", "bank_amount", "matched_invoice",
        "invoice_amount", "amount_difference", "date_difference_days",
        "confidence", "margin", "status", "correct"
    ]
    if column in results.columns
]

st.dataframe(results[display_columns], use_container_width=True, hide_index=True)


# ============================================================
# EXPORT
# ============================================================

st.write("")
st.markdown(
    '<div class="section-header">Export</div>',
    unsafe_allow_html=True
)

csv_data = results.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download evaluated results (.csv)",
    data=csv_data,
    file_name="evaluated_results.csv",
    mime="text/csv"
)


# ============================================================
# FOOTER
# ============================================================

st.write("")
st.markdown(
    '<hr><p style="color: #4A5568; font-size: 13px;">'
    'AI Finance Controller — deterministic reconciliation with selective AI investigation.'
    '</p>',
    unsafe_allow_html=True
)