from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np

from ticketroute.language import detect_language
from ticketroute.llm import llm_triage
from ticketroute.preprocess import normalize
from ticketroute.reply import draft_reply
from ticketroute.similar import similar_tickets
from ticketroute.taxonomy import ABSTAIN_THRESHOLD

ROOT = Path(__file__).resolve().parent.parent
MODELS = ROOT / "models"

_dept = None
_urg = None


def load_models():
    global _dept, _urg
    if _dept is None:
        _dept = joblib.load(MODELS / "department.joblib")
        _urg = joblib.load(MODELS / "urgency.joblib")
    return _dept, _urg


def _top(clf, text: str) -> tuple[str, float, list[tuple[str, float]]]:
    proba = clf.predict_proba([text])[0]
    classes = list(clf.classes_)
    order = np.argsort(proba)[::-1]
    ranked = [(classes[i], float(proba[i])) for i in order]
    return ranked[0][0], ranked[0][1], ranked[:3]


def _local_predict(raw: str) -> dict:
    text = normalize(raw)
    lang = detect_language(raw)
    dept_clf, urg_clf = load_models()
    dept, dept_p, dept_top = _top(dept_clf, text)
    urg, urg_p, urg_top = _top(urg_clf, text)
    conf = float(min(dept_p, urg_p))
    needs_human = conf < ABSTAIN_THRESHOLD
    reply = draft_reply(dept, urg, lang, ticket=raw)
    return {
        "text": raw,
        "language": lang,
        "department": dept,
        "department_confidence": round(dept_p, 3),
        "department_top3": dept_top,
        "urgency": urg,
        "urgency_confidence": round(urg_p, 3),
        "urgency_top3": urg_top,
        "confidence": round(conf, 3),
        "needs_human": needs_human,
        "suggested_reply": reply,
        "source": "sklearn",
        "llm_backend": "none",
        "llm_error": None,
        "rationale": "",
        "similar": similar_tickets(raw, k=3),
    }


def predict_ticket(text: str, use_llm: bool = True) -> dict:
    raw = text
    base = _local_predict(raw)
    if not use_llm:
        return base
    llm = llm_triage(
        raw,
        {
            "department": base["department"],
            "department_confidence": base["department_confidence"],
            "urgency": base["urgency"],
            "urgency_confidence": base["urgency_confidence"],
            "language": base["language"],
        },
    )
    base["llm_backend"] = llm.get("backend") or "none"
    base["llm_error"] = llm.get("error")
    if not llm.get("used"):
        return base
    base["language"] = llm["language"]
    base["department"] = llm["department"]
    base["urgency"] = llm["urgency"]
    base["department_confidence"] = llm["department_confidence"]
    base["urgency_confidence"] = llm["urgency_confidence"]
    base["confidence"] = round(min(llm["department_confidence"], llm["urgency_confidence"]), 3)
    base["needs_human"] = bool(llm["needs_human"] or base["confidence"] < ABSTAIN_THRESHOLD)
    base["suggested_reply"] = llm["suggested_reply"]
    base["rationale"] = llm.get("rationale") or ""
    base["source"] = "llm+" + str(llm.get("backend"))
    return base
