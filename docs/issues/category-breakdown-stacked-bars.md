# Bug: Category Breakdown bar graph stacks "total" and "eligible" incorrectly

## Problem

The Category Breakdown bar graph (`src/hsa_ledger/ui.py:79`) renders the `total` and `eligible` bars in a **stacked** configuration instead of side-by-side grouped bars.

**Current code:**
```python
st.bar_chart(cat_df.set_index("category")[["total", "eligible"]])
```

**Visual issue:**
- `color: total` and `color: eligible` are stacked on top of each other
- This gives the false impression that total + eligible is being shown
- Users cannot easily visually compare total vs eligible per category

## Root Cause

Streamlit's `st.bar_chart()` wraps Altair/Vega-Lite, which defaults `stack="zero"` when multiple color-coded series exist on bar marks. This causes stacking instead of grouping.

## Proposed Solution

### Option A (preferred - Streamlit >= 1.36)

Use the `stack=False` parameter:

```python
st.bar_chart(
    cat_df.set_index("category")[["total", "eligible"]],
    stack=False,
)
```

### Option B (backward compatible with older Streamlit)

Use Altair directly with `xOffset` for explicit grouped bars:

```python
import altair as alt

cat_melted = cat_df.melt(
    id_vars=["category"],
    value_vars=["total", "eligible"],
    var_name="type",
    value_name="amount",
)

chart = alt.Chart(cat_melted).mark_bar().encode(
    x=alt.X("category:N", title="Category"),
    y=alt.Y("amount:Q", title="Amount ($)"),
    color=alt.Color("type:N", title="Amount Type"),
    xOffset=alt.XOffset("type:N"),
)

st.altair_chart(chart, use_container_width=True)
```

## Acceptance Criteria

- [ ] For each category, the "total" bar shows the total amount
- [ ] For each category, the "eligible" bar shows the HSA-eligible amount
- [ ] Bars are side-by-side (grouped), not stacked
- [ ] The chart visually reads as "total vs eligible" not "total + eligible"

## Files to Touch

- `src/hsa_ledger/ui.py` (line ~79)

## Notes

First, check which Streamlit version is specified in dependencies to decide between Option A and Option B.
