"""
Category Search Autocomplete — interactive prototype
======================================================

Run with:
    pip install streamlit pandas
    streamlit run streamlit_app.py

What this shows, side by side:
  - BEFORE: today's production behaviour (substring match, no relevance
    scoring — a category can rank first just by matching, regardless of
    how good the match is).
  - AFTER: the proposed fix (match-quality tier, with real search
    frequency from BigQuery breaking ties within a tier).

Two data modes:
  - "Real production data" — genuine numbers pulled from BigQuery
    (woven-bonbon-90705.db_events_internal.sell_actions,
    event list_category_tapped), SCOPED TO SINGAPORE (country = 'SG').
    See real_data.py for the exact query.
  - "Synthetic playground" — type ANY search text and see the logic run
    against a small made-up category list, useful for testing edge cases
    that aren't in the real dataset.

Companion doc: RFC - CATEGORY SEARCH AUTOCOMPLETE (Confluence)
"""

import pandas as pd
import streamlit as st

from matching import build_candidates, buggy_order, fixed_order, TIER_LABELS
from real_data import EXAMPLE_QUERIES, FREQUENCY_LOOKUP, SYNTHETIC_CATEGORIES, real_categories_for_query

st.set_page_config(page_title="Category Search Autocomplete — prototype", layout="wide")

st.markdown(
    """
    <style>
    .flow-box {
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 8px;
        font-size: 0.92rem;
    }
    .flow-neutral { background: #EEF2F8; border-left: 4px solid #2E5EAA; }
    .flow-bad     { background: #FCEEEE; border-left: 4px solid #B23B3B; }
    .flow-good    { background: #EAF6EE; border-left: 4px solid #1E8449; }
    .rank-1 { font-weight: 700; color: #1E8449; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Category Search Autocomplete")
st.caption(
    "Prototype for the RFC — showing today's buggy ranking vs. the proposed "
    "tier + search-frequency fix, with real Carousell production data "
    "scoped to Singapore (SG)."
)

# ---------------------------------------------------------------------------
# Data mode + query input
#
# Both modes are free-text now. In "real" mode, matching always runs
# against the FULL real SG category universe (category_universe.py) —
# frequency for a (query, category) pair defaults to 0 when we don't have
# a real count for it, rather than the category not being a candidate at
# all. That's what previously made typing e.g. "bicycle" (vs. the ~14
# preset short queries we have rich data for) make everything vanish.
#
# The category universe and frequency numbers are filtered to
# country = 'SG' — earlier versions used the global (all-market) numbers,
# which surfaced Indonesian-market categories like "Aksesoris Mobil" and
# "Barang Yang Dicari" in what's meant to be an SG-scoped demo.
# ---------------------------------------------------------------------------
mode = st.radio(
    "Data source",
    ["Real production data (BigQuery, Singapore)", "Synthetic playground (type anything)"],
    horizontal=True,
)
is_real = mode.startswith("Real")

if "query_input" not in st.session_state:
    st.session_state.query_input = "bi"

if is_real:
    st.caption(
        "Matches against the real Carousell **Singapore** category list (~600 categories). "
        "Frequency is a genuine `times_selected` count from BigQuery (country = 'SG') where we "
        "have one for this exact search term, and **0** otherwise — a missing "
        "frequency no longer removes the category as a candidate."
    )
    CHIPS_PER_ROW = 7
    for row_start in range(0, len(EXAMPLE_QUERIES), CHIPS_PER_ROW):
        row_queries = EXAMPLE_QUERIES[row_start:row_start + CHIPS_PER_ROW]
        chip_cols = st.columns(CHIPS_PER_ROW)
        for col, q in zip(chip_cols, row_queries):
            if col.button(q, key=f"chip_{q}", width="stretch"):
                st.session_state.query_input = q
else:
    st.caption(
        "Category list and popularity numbers here are illustrative (not real "
        "traffic) — good for testing arbitrary edge cases."
    )

query = st.text_input("Type a search query:", key="query_input")

if not query.strip():
    st.warning("Type a search query to see results.")
    st.stop()

if is_real:
    categories = real_categories_for_query(query)
    has_real_freq = any(v > 0 for (q, _), v in FREQUENCY_LOOKUP.items() if q == query.lower())
    if not has_real_freq:
        st.info(
            f'No real Singapore search-frequency data for "{query}" specifically — every match below '
            f'defaults to frequency 0, so ranking falls back to tier alone. Try one of the '
            f'example chips above for a query with rich real frequency data.'
        )
else:
    categories = SYNTHETIC_CATEGORIES

candidates = build_candidates(query, categories)
before = buggy_order(candidates)
after = fixed_order(candidates)

# ---------------------------------------------------------------------------
# Backend flow — what actually happens, step by step.
# Collapsed by default so the ranked results (the part people actually
# want to see first) show immediately without scrolling past this.
# ---------------------------------------------------------------------------
with st.expander(f"What happens in the backend — {len(before)} of {len(candidates)} category names checked", expanded=False):
    step1, step2 = st.columns(2)
    with step1:
        st.markdown(
            f'<div class="flow-box flow-neutral"><b>1. Request</b><br>'
            f'User types <code>&quot;{query}&quot;</code> into the category search box.</div>',
            unsafe_allow_html=True,
        )
    with step2:
        st.markdown(
            f'<div class="flow-box flow-neutral"><b>2. Candidate matching</b><br>'
            f'Every category whose name contains <code>&quot;{query}&quot;</code> (case-insensitive) '
            f'becomes a candidate — {len(before)} out of {len(candidates)} category names checked.</div>',
            unsafe_allow_html=True,
        )

    flow_before, flow_after = st.columns(2)
    with flow_before:
        st.markdown(
            '<div class="flow-box flow-bad"><b>3a. BEFORE — ranking (current)</b><br>'
            'No scoring step. Candidates are returned in whatever order the '
            'query/index gives them back — modeled here as alphabetical, same as a '
            'plain <code>WHERE name LIKE %query% ORDER BY name</code>.</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="flow-box flow-bad"><b>4a. BEFORE — response</b><br>'
            'List is sent back to the app as-is. Whether the best match lands on '
            'top is pure luck.</div>',
            unsafe_allow_html=True,
        )
    with flow_after:
        st.markdown(
            '<div class="flow-box flow-good"><b>3b. AFTER — tier assignment</b><br>'
            'Each candidate is scored 0 (exact) → 3 (query buried mid-word), '
            'based on <i>where</i> the match happened.</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="flow-box flow-good"><b>4b. AFTER — frequency lookup</b><br>'
            'For ties within a tier, look up how often that (query, category) pair '
            'was actually picked before — a small precomputed table refreshed by a '
            'nightly BigQuery batch job, not computed live.</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="flow-box flow-good"><b>5b. AFTER — response</b><br>'
            'Candidates sorted by <code>(tier, -frequency)</code> and sent back — '
            'best text match first, popularity breaks any tie.</div>',
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# Side-by-side ranked results — the main event, shown in full right away.
# ---------------------------------------------------------------------------
st.subheader(f'Ranked results for "{query}"')
col_before, col_after = st.columns(2)

with col_before:
    st.markdown("#### 🔴 Before (current)")
    if not before:
        st.write("No matches.")
    for i, c in enumerate(before, 1):
        cls = "rank-1" if i == 1 else ""
        st.markdown(
            f'<span class="{cls}">{i}. {c.name}</span>  '
            f'<span style="color:#888">(freq {c.freq})</span>',
            unsafe_allow_html=True,
        )

with col_after:
    st.markdown("#### 🟢 After (proposed fix)")
    if not after:
        st.write("No matches.")
    for i, c in enumerate(after, 1):
        cls = "rank-1" if i == 1 else ""
        st.markdown(
            f'<span class="{cls}">{i}. {c.name}</span>  '
            f'<span style="color:#888">(tier {c.tier} · freq {c.freq})</span>',
            unsafe_allow_html=True,
        )

if before and after and before[0].name != after[0].name:
    st.success(
        f'Top result changes from **"{before[0].name}"** to **"{after[0].name}"** '
        f'once tier + frequency are applied.'
    )
elif before and after:
    st.info('Top result is unchanged for this query — the fix mainly reorders further down the list.')

# ---------------------------------------------------------------------------
# Full trace table — every MATCHED candidate, every stage
#
# Only candidates that actually matched the query are shown here. In real
# mode, `candidates` includes the full ~600-category SG universe (most of
# which never match a given query at all) — showing every non-match
# alongside the handful of real matches is just noise. Non-matches were
# already excluded from the before/after ranked lists above; this just
# makes the trace table consistent with that.
# ---------------------------------------------------------------------------
with st.expander("Full trace — every matched category, every stage of the pipeline"):
    matched_candidates = [c for c in candidates if c.matched]
    if not matched_candidates:
        st.write("No categories matched this query.")
    else:
        rows = []
        for c in matched_candidates:
            rows.append({
                "category": c.name,
                "tier": str(c.tier),
                "tier meaning": TIER_LABELS[c.tier],
                "frequency (times_selected)": c.freq,
                "before rank": str(before.index(c) + 1) if c in before else "—",
                "after rank": str(after.index(c) + 1) if c in after else "—",
            })
        df = pd.DataFrame(rows).sort_values(by="tier")
        st.dataframe(df, width="stretch", hide_index=True)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.divider()
st.caption(
    "Source: `woven-bonbon-90705.db_events_internal.sell_actions`, event "
    "`list_category_tapped`, country = 'SG', Jun 1 – Sep 1 2026. "
    "Full writeup: RFC - CATEGORY SEARCH AUTOCOMPLETE (Confluence)."
)
