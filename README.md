# Category Search Autocomplete — Streamlit prototype

Interactive demo for the RFC: shows today's buggy category-search ranking
next to the proposed tier + search-frequency fix, with real Carousell
production data (not synthetic), scoped to Singapore (country = 'SG').

## Run it

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Opens at http://localhost:8501.

## Files

- `matching.py` — the actual ranking logic (tier classification, buggy vs.
  fixed sort). This is the part worth reading/porting; everything else is UI.
- `category_universe.py` — ~600 real Singapore Carousell category names
  (from the same BigQuery table, filtered to country = 'SG'). This is the
  full pool every search matches against, regardless of query. An earlier
  version used the global (all-market) category list, which surfaced
  Indonesian-market categories like "Aksesoris Mobil" (Car Accessories) and
  "Barang Yang Dicari" (Wanted Items) in what's meant to be an SG demo.
- `real_data.py` — real `(query, category) -> times_selected` counts from
  BigQuery, SG only, for ~14 search terms, plus a small synthetic category
  list for the playground mode. A pair with no real count correctly
  defaults to frequency 0 rather than the category not being a candidate
  at all.
- `streamlit_app.py` — the app itself: type any search term, see the
  before/after ranked lists in full immediately, with the backend-pipeline
  explanation and the full per-category trace table both tucked into
  collapsed expanders below (click to open either one). Example chips are
  shortcuts to terms with rich real SG frequency data.

## Companion pieces

- RFC doc (Confluence): *RFC - CATEGORY SEARCH AUTOCOMPLETE*
- Browser-based version of this same demo (no install needed): published as
  a Claude Artifact — good for a quick screen-share, this Streamlit app is
  better for live tinkering / projecting during the actual discussion.
