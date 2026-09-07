"""
Real Carousell production data, pulled from BigQuery on 2026-09-07,
SCOPED TO SINGAPORE (country = 'SG').

Source table: woven-bonbon-90705.db_events_internal.sell_actions
Event:        list_category_tapped
              (fires when a user types into the sell-form category search
              and then taps a category — i.e. "searched X, picked Y")
Window:       2026-06-01 to 2026-09-01
Filter:       country = 'SG'

Earlier versions of this file mixed in every Carousell market (SG, ID, MY,
PH, HK, TW), which is why examples like "gu" -> "Pergudangan dan Logistic"
(Indonesian for "Warehousing") showed up in what was meant to be an SG
demo. Every number below is now genuinely SG-only.

This file has two SEPARATE things, kept deliberately separate:

  1. FREQUENCY_LOOKUP — a (query, category_name) -> times_selected dict.
     This is necessarily sparse: it only has a real number for combinations
     someone has actually searched before. Looking up a pair that isn't
     here should default to 0 (a category with no observed search-frequency
     yet), NOT be treated as "this category doesn't exist" — that
     conflation was an earlier bug (see category_universe.py docstring).

  2. EXAMPLE_QUERIES — the search terms we happen to have rich, real SG
     frequency data for, used for the demo's one-click example chips.

The actual category *candidates* to match against come from
category_universe.py (CATEGORY_UNIVERSE) — always the full list,
regardless of query.
"""

from category_universe import CATEGORY_UNIVERSE

# (query, category_name) -> real times_selected count. SG only.
FREQUENCY_LOOKUP = {}


def _load(query, pairs):
    for name, freq in pairs:
        FREQUENCY_LOOKUP[(query, name)] = freq


# The four searches from the original bug report — SG-only breakdown.
# Note: SG's real taxonomy doesn't have a plain "Cars" or "Cars for Sale"
# category (SG uses "Used Cars" / "New Cars" / "Car Rental" etc.), and
# volume on these specific 2-3 letter queries is much lower in SG alone
# than in the combined-market numbers — that's expected, not a bug.
_load("car", [
    ("Other Car Services", 44), ("Other Car Parts", 39), ("Car Rental", 29),
    ("Used Cars", 21), ("Car Seats", 16), ("Scarves", 1),
])
_load("bi", [
    ("Bicycles", 26), ("Parts & Accessories", 14), ("E-Scooters & E-Bikes", 5),
    ("Bikinis & Swimsuits", 1),
])
_load("la", [
    ("Laptops & Notebooks", 3), ("Sunglasses & Eyewear", 1),
])
_load("wa", [
    ("Watches", 8), ("Women's Watches", 3), ("Men's Watches", 2),
    ("Wall Decor Accessories", 1), ("Waste Bins & Bags", 1),
    ("Washing Machines and Dryers", 1), ("Warehouse & Logistics", 1),
])

# Broader set: the highest-volume short (2-6 char) search queries on the
# SG sell-form category picker, real production numbers, top 5 per query.
_load("bag", [
    ("Shoulder Bags", 654), ("Cross-body Bags", 589), ("Tote Bags", 429),
    ("Bags & Wallets", 285), ("Backpacks", 219),
])
_load("card", [
    ("Raw Cards", 867), ("Card Boxes & Cases", 499), ("Card Packs", 287),
    ("Trading Cards Accessories", 218), ("Raw Singles", 150),
])
_load("chairs", [
    ("Chairs", 2139), ("Baby High Chairs", 2), ("Tables & Sets", 1),
    ("Kids' Tables & Chairs", 1), ("Wheelchairs", 1),
])
_load("fan", [
    ("Fans", 308), ("Other Merchandise", 308), ("Character Goods", 266),
    ("Fan Merchandise", 94), ("K-Wave Merchandise", 66),
])
_load("lego", [
    ("Lego & Building Sets", 997), ("Toys & Games", 4),
    ("Flowers & Bouquets", 1), ("Vehicle & Diecast Models", 1),
])
_load("pet", [
    ("Homes & Other Pet Accessories", 1226), ("Pet Care Services", 110),
    ("Pet Food", 78), ("Health & Grooming", 45), ("Health & Grooming Supplies", 37),
])
_load("raw", [
    ("Raw Singles", 2073), ("Raw Cards", 1506),
])
_load("sofas", [
    ("Sofas", 1014),
])
_load("toy", [
    ("Designer & Blind Box Toys", 862), ("Action & Battle Toys", 709),
    ("Toys & Games", 401), ("Plushies & Soft Toys", 335),
    ("Interactive Toys", 255),
])
_load("toys", [
    ("Toys & Games", 635), ("Figurines & Statues", 445),
    ("Designer & Blind Box Toys", 415), ("Plushies & Soft Toys", 285),
    ("Action & Battle Toys", 255),
])

EXAMPLE_QUERIES = ["car", "bi", "la", "wa", "bag", "card", "chairs", "fan",
                    "lego", "pet", "raw", "sofas", "toy", "toys"]

# Small synthetic universe (independent of real data) for the "playground"
# mode, where popularity numbers are illustrative rather than real.
SYNTHETIC_CATEGORIES = [
    ("Cars", 950), ("Car Accessories", 400), ("Scarves", 120),
    ("Motorcycles", 300), ("Bicycles", 500), ("Waste Paper Bins", 20),
    ("Waste Bins", 15), ("Laptops & Computers", 800), ("Ladders", 60),
    ("Watches", 700), ("Cameras", 650), ("Cardigans", 90),
]


def real_categories_for_query(query: str):
    """The full real SG category universe, each paired with its real search
    frequency for this exact query if we have one, else 0. This is what
    fixes the 'category vanishes' bug: the candidate list never depends on
    whether we happen to have frequency data for this query."""
    q = query.lower()
    return [(name, FREQUENCY_LOOKUP.get((q, name), 0)) for name in CATEGORY_UNIVERSE]
