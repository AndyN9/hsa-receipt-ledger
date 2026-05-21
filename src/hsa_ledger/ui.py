import os
import streamlit as st
import pandas as pd
from hsa_ledger.database import init_db, get_all_records, get_stats

st.set_page_config(page_title="HSA Receipt Ledger", layout="wide")

DB_PATH = os.environ.get("HSA_LEDGER_DB", os.path.join(os.getcwd(), "hsa_ledger.db"))
VAULT_PATH = os.environ.get("HSA_LEDGER_VAULT", os.path.join(os.getcwd(), "hsa_vault"))

conn = init_db(DB_PATH)

st.title("HSA Receipt Ledger")

stats = get_stats(conn)
col1, col2, col3 = st.columns(3)
col1.metric("Total Records", stats["total_records"])
col2.metric("Unreimbursed Total", f"${stats['unreimbursed_total']:.2f}")
col3.metric("Total HSA Eligible", f"${stats['total_hsa_eligible']:.2f}")

records = get_all_records(conn)
if not records:
    st.info("No records in the ledger yet.")
else:
    df = pd.DataFrame(records)

    st.subheader("Search")
    search = st.text_input("Search by provider, category, or text")
    if search:
        mask = (
            df["provider"].str.contains(search, case=False, na=False, regex=False)
            | df["category"].str.contains(search, case=False, na=False, regex=False)
            | df["extracted_text"].str.contains(search, case=False, na=False, regex=False)
        )
        df = df[mask]

    st.subheader("Transactions")
    display_cols = [
        "transaction_date", "provider", "patient_name", "category",
        "total_amount", "hsa_eligible_amount", "is_reimbursed",
        "reimbursement_date",
    ]
    st.dataframe(
        df[display_cols],
        use_container_width=True,
        hide_index=True,
        column_config={
            "total_amount": st.column_config.NumberColumn(format="$%.2f"),
            "hsa_eligible_amount": st.column_config.NumberColumn(format="$%.2f"),
            "is_reimbursed": st.column_config.CheckboxColumn(),
        },
    )

    st.subheader("Category Breakdown")
    cat_df = df.groupby("category").agg(
        total=("total_amount", "sum"),
        eligible=("hsa_eligible_amount", "sum"),
        count=("id", "count"),
    ).reset_index()
    st.bar_chart(cat_df.set_index("category")[["total", "eligible"]])

    st.subheader("Reimbursement Tracker")
    total_banked = df["hsa_eligible_amount"].sum()
    total_reimbursed = df[df["is_reimbursed"] == 1]["hsa_eligible_amount"].sum()
    reimb_df = pd.DataFrame({
        "Status": ["Banked", "Reimbursed"],
        "Amount": [total_banked - total_reimbursed, total_reimbursed],
    })
    st.bar_chart(reimb_df.set_index("Status"))

inbox = os.path.join(VAULT_PATH, "inbox")
if os.path.isdir(inbox):
    inbox_files = [
        f for f in os.listdir(inbox)
        if os.path.isfile(os.path.join(inbox, f)) and not f.startswith(".")
    ]
    if inbox_files:
        st.subheader("Inbox (Unprocessed Files)")
        for f in inbox_files:
            st.text(f"  {f}")

conn.close()
