# Enhancement: Search & Pagination for Receipt Previews

## Problem

The Receipts section (`src/hsa_ledger/ui.py:58-71`) renders an expandable image preview for **every** transaction in the filtered dataset. On a ledger with hundreds of records, this means:

- All expanders are rendered at once, slowing initial page load
- Users must scroll through every receipt to find one they care about
- No way to search within receipt content (only the transaction-level search above the table)

## Proposed Solution

### 1. Pagination

Add page-based navigation to the Receipts section so only N receipts are rendered at a time.

**UX:**
- Show `st.selectbox` or `st.number_input` for page size (e.g., 10, 25, 50)
- Show "Page X of Y" with prev/next buttons below the expanders
- Only render the expanders for the current page

**Implementation sketch:**

```python
page_size = st.selectbox("Receipts per page", [10, 25, 50], key="receipt_page_size")
total_pages = max(1, (len(receipt_rows) + page_size - 1) // page_size)
page = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
start = (page - 1) * page_size
end = start + page_size

for _, row in receipt_rows.iloc[start:end].iterrows():
    ...
```

### 2. Search

Add a search bar scoped to the Receipts section that filters by provider, date, or file name.

**UX:**
- Text input above the pagination controls: "Search receipts by provider or file name"
- Filters the receipt rows in-memory before paginating

**Implementation sketch:**

```python
receipt_search = st.text_input("Search receipts by provider or file name", key="receipt_search")
receipt_rows = df[df["file_path"].notna()]
if receipt_search:
    mask = (
        receipt_rows["provider"].str.contains(receipt_search, case=False, na=False)
        | receipt_rows["file_name"].str.contains(receipt_search, case=False, na=False)
    )
    receipt_rows = receipt_rows[mask]
```

## Acceptance Criteria

- [ ] With 50+ transactions, the Receipts section loads without noticeable delay
- [ ] Pagination controls show correct page count and navigate correctly
- [ ] Search filters receipts independently of the main transaction search
- [ ] Edge case: zero matching receipts shows "No receipts found" instead of empty expanders
- [ ] Edge case: search + pagination compose correctly (search reduces total, pagination slices current page)

## Files to Touch

- `src/hsa_ledger/ui.py`

## Out of Scope

- Server-side pagination (all filtering is in-memory on the already-loaded DataFrame)
- Thumbnail grid view instead of expanders
- Drag-and-drop reordering
