from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np

from ticketroute.explain import token_highlight
from ticketroute.language import detect_language
from ticketroute.llm import llm_polish
from ticketroute.preprocess import normalize
from ticketroute.reply import draft_reply
from ticketroute.similar import similar_tickets
from ticketroute.taxonomy import (
    ABSTAIN_DEPARTMENT,
    ABSTAIN_THRESHOLD,
    SLA_HOURS,
)

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


def predict_ticket(
    text: str,
    use_llm: bool = True,
    channel: str = "web",
    ext_id: str | None = None,
    persist: bool = False,
) -> dict:
    raw = text
    norm = normalize(raw)
    lang = detect_language(raw)
    dept_clf, urg_clf = load_models()
    dept, dept_p, dept_top = _top(dept_clf, norm)
    urg, urg_p, urg_top = _top(urg_clf, norm)
    conf = float(min(dept_p, urg_p))
    needs_human = conf < ABSTAIN_THRESHOLD or lang == "other"
    if needs_human and conf < ABSTAIN_THRESHOLD:
        dept = ABSTAIN_DEPARTMENT
    sla = int(SLA_HOURS.get(urg, 24))
    template = draft_reply(dept, urg, lang, ticket=raw)
    reply = template
    llm_backend = "none"
    llm_error = None
    rationale = ""
    source = "sklearn"
    if use_llm and lang != "other":
        polished = llm_polish(raw, lang, dept, urg, template)
        llm_backend = polished.get("backend") or "none"
        llm_error = polished.get("error")
        if polished.get("used"):
            reply = polished["suggested_reply"]
            rationale = polished.get("rationale") or ""
            source = "sklearn+llm:" + str(llm_backend)
    out = {
        "text": raw,
        "ext_id": ext_id,
        "channel": channel,
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
        "template_reply": template,
        "source": source,
        "llm_backend": llm_backend,
        "llm_error": llm_error,
        "rationale": rationale,
        "similar": similar_tickets(raw, k=3),
        "explain": token_highlight(raw),
        "sla_hours": sla,
    }
    if persist:
        from ticketroute.store import insert_ticket

        insert_ticket(out)
    return out
