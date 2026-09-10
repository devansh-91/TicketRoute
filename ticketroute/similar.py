"""Nearest labelled tickets via TF-IDF cosine (no extra deps)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ticketroute.preprocess import normalize

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "tickets.csv"

_vec = None
_mat = None
_df = None


def _load():
    global _vec, _mat, _df
    if _vec is not None:
        return
    if not DATA.exists():
        _df = pd.DataFrame(columns=["text", "department", "urgency", "language"])
        _vec = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        _mat = _vec.fit_transform([""])
        return
    _df = pd.read_csv(DATA)
    texts = _df["text"].fillna("").map(normalize).tolist()
    _vec = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=20000)
    _mat = _vec.fit_transform(texts)


def similar_tickets(text: str, k: int = 3) -> list[dict]:
    _load()
    assert _vec is not None and _mat is not None and _df is not None
    if _df.empty or not str(text).strip():
        return []
    q = _vec.transform([normalize(text)])
    scores = cosine_similarity(q, _mat).ravel()
    # skip near-exact self matches later by text equality
    order = scores.argsort()[::-1]
    out = []
    needle = normalize(text)
    for i in order:
        row = _df.iloc[int(i)]
        body = str(row.get("text", ""))
        if normalize(body) == needle:
            continue
        out.append(
            {
                "text": body[:240],
                "department": str(row.get("department", "")),
                "urgency": str(row.get("urgency", "")),
                "language": str(row.get("language", "")),
                "score": round(float(scores[int(i)]), 3),
            }
        )
        if len(out) >= k:
            break
    return out
