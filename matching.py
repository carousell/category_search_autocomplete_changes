"""
Core matching/ranking logic shared by the demo. This is the exact logic
from the RFC (Category Search Autocomplete) — kept as one small, pure,
dependency-free module so it's easy to read, test, and port to Swift/Kotlin.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

TIER_LABELS = {
    0: "Exact match",
    1: "Name starts with query",
    2: "A word inside the name starts with query",
    3: "Query appears somewhere in the name",
}


@dataclass
class Candidate:
    name: str
    freq: int
    matched: bool
    tier: Optional[int]

    @property
    def tier_label(self) -> str:
        return TIER_LABELS.get(self.tier, "No match")


def classify(query: str, name: str) -> Optional[int]:
    """Returns the match tier (0=best .. 3=worst), or None if no match at all."""
    q, n = query.lower(), name.lower()
    if q not in n:
        return None
    if n == q:
        return 0
    if n.startswith(q):
        return 1
    if any(word.startswith(q) for word in n.split()):
        return 2
    return 3


def build_candidates(query: str, categories: List[Tuple[str, int]]) -> List[Candidate]:
    out = []
    for name, freq in categories:
        tier = classify(query, name)
        out.append(Candidate(name=name, freq=freq, matched=tier is not None, tier=tier))
    return out


def buggy_order(candidates: List[Candidate]) -> List[Candidate]:
    """Current production behaviour: match, then whatever order they came back
    in — modeled here as alphabetical, same as a naive
    'WHERE name LIKE %query% ORDER BY name' would give you."""
    matched = [c for c in candidates if c.matched]
    return sorted(matched, key=lambda c: c.name.lower())


def fixed_order(candidates: List[Candidate]) -> List[Candidate]:
    """Proposed behaviour: tier first (match quality), frequency breaks ties."""
    matched = [c for c in candidates if c.matched]
    return sorted(matched, key=lambda c: (c.tier, -c.freq))


def score_match(query: str, name: str, popularity_lookup: dict):
    """The (query, category)-keyed tuple-scoring version from the RFC (section 9)."""
    q, n = query.lower(), name.lower()
    if n == q:
        text_tier = 0
    elif n.startswith(q):
        text_tier = 1
    elif any(w.startswith(q) for w in n.split()):
        text_tier = 2
    elif q in n:
        text_tier = 3
    else:
        return None
    popularity = popularity_lookup.get((q, name), 0)
    return (text_tier, -popularity)
