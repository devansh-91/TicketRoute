"""Cheap token overlap explanation (no SHAP dependency)."""
from __future__ import annotations

import re
from collections import Counter

from ticketroute.preprocess import normalize

STOP = {
    "the", "a", "an", "to", "of", "and", "or", "in", "on", "for", "is", "it",
    "my", "me", "i", "please", "pls", "hai", "ho", "ke", "ki", "ka", "me",
}


def token_highlight(text: str, n: int = 8) -> list[str]:
    t = normalize(text).lower()
    toks = re.findall(r"[a-zA-Z\u0900-\u097F']+", t)
    toks = [w for w in toks if w not in STOP and len(w) > 2]
    counts = Counter(toks)
    return [w for w, _ in counts.most_common(n)]
