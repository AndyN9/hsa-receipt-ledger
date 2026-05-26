import os
import streamlit as st
import pandas as pd
from hsa_ledger.database import init_db, get_all_records, get_stats


def _is_image_path(file_path: str) -> bool:
    return file_path.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))


def _filter_receipt_rows(df: pd.DataFrame, search: str = "") -> pd.DataFrame:
    rows = df[df["file_path"].notna()].copy()
    if search:
        mask = (
            rows["provider"].str.contains(search, case=False, na=False, regex=False)
            | rows["file_name"].str.contains(search, case=False, na=False, regex=False)
        )
        rows = rows[mask]
    return rows


def _pagination_info(total: int, page: int, page_size: int) -> dict:
    total_pages = max(1, (total + page_size - 1) // page_size)
    clamped = max(1, min(page, total_pages))
    start = (clamped - 1) * page_size
    end = start + page_size
    return {"page": clamped, "start": start, "end": end, "total_pages": total_pages}


def _resolve_page_on_search(new_search: str, prev_search: str, current_page: int) -> int:
    return 1 if new_search != prev_search else current_page


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
        width='stretch',
        hide_index=True,
        column_config={
            "total_amount": st.column_config.NumberColumn(format="$%.2f"),
            "hsa_eligible_amount": st.column_config.NumberColumn(format="$%.2f"),
            "is_reimbursed": st.column_config.CheckboxColumn(),
        },
    )

    st.subheader("Receipts")
    receipt_search = st.text_input("Search receipts by provider or file name", key="receipt_search")

    receipt_rows = _filter_receipt_rows(df, receipt_search)

    if receipt_rows.empty:
        st.info("No receipts found.")
    else:
        page_size = st.session_state.get("receipt_page_size", 10)

        st.session_state.setdefault("receipt_page", 1)

        st.session_state.receipt_page = _resolve_page_on_search(
            receipt_search, st.session_state.get("prev_receipt_search", ""), st.session_state.receipt_page
        )
        if receipt_search != st.session_state.get("prev_receipt_search", ""):
            st.session_state.prev_receipt_search = receipt_search

        info = _pagination_info(len(receipt_rows), st.session_state.receipt_page, page_size)
        page = info["page"]
        start = info["start"]
        end = info["end"]
        total_pages = info["total_pages"]

        for _, row in receipt_rows.iloc[start:end].iterrows():
            fp = row.get("file_path")
            if fp and os.path.exists(fp):
                label = f"{row.get('provider', 'Unknown')} — {row.get('transaction_date', '')}"
                with st.expander(label):
                    if _is_image_path(fp):
                        st.image(fp, width='stretch')
                    else:
                        with open(fp, "rb") as f:
                            st.download_button(
                                "Download Receipt", f.read(),
                                file_name=row.get("file_name", "receipt"),
                            )

        _, mid, _ = st.columns([1, 2, 1])
        with mid:
            pag_cols = st.columns([1, 1, 1, 1])
            with pag_cols[0]:
                st.selectbox("Per page", [10, 25, 50], key="receipt_page_size", label_visibility="collapsed")
            with pag_cols[1]:
                if st.button("◀ Prev", key="prev_page", disabled=(page <= 1)):
                    st.session_state.receipt_page -= 1
            with pag_cols[2]:
                st.write(f"Page {page} of {total_pages}")
            with pag_cols[3]:
                if st.button("Next ▶", key="next_page", disabled=(page >= total_pages)):
                    st.session_state.receipt_page += 1

    st.subheader("Category Breakdown")
    cat_df = df.groupby("category").agg(
        total=("total_amount", "sum"),
        eligible=("hsa_eligible_amount", "sum"),
        count=("id", "count"),
    ).reset_index()
    st.bar_chart(cat_df.set_index("category")[["total", "eligible"]], stack=False)

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
