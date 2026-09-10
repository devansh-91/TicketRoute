"""Groq (preferred) or Ollama LLM for structured routing + reply polish."""
from __future__ import annotations

import json
import re
from typing import Any

import httpx

from ticketroute.config import (
    GROQ_MODEL,
    LLM_TIMEOUT,
    OLLAMA_HOST,
    OLLAMA_MODEL,
    groq_key_present,
)
from ticketroute.taxonomy import DEPARTMENTS, LANGUAGES, URGENCY

SYSTEM = """You are TicketRoute, an Indian customer-support triage assistant.
Return ONLY valid JSON (no markdown) with keys:
language: one of en, hi, hinglish
department: one of the exact department strings given
urgency: one of P1, P2, P3, P4
department_confidence: number 0-1
urgency_confidence: number 0-1
needs_human: boolean (true if unsure, fraud/safety, or missing facts)
suggested_reply: a short first reply in the ticket's language. Be specific to the ticket. Do not invent refunds, amounts, or legal conclusions. Include the SLA hours.
rationale: one sentence why you chose department and urgency.

Urgency:
P1 critical — fraud, account takeover, safety, payment captured but service dead, complete outage
P2 high — cannot login, failed payment, data missing, repeated failures
P3 normal — how-to, delay, feature request with workaround
P4 low — thanks, FYI, suggestion
"""


def _extract_json(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t)
        t = re.sub(r"\s*```$", "", t)
    try:
        obj = json.loads(t)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", t, re.S)
        if not m:
            return None
        try:
            obj = json.loads(m.group(0))
            return obj if isinstance(obj, dict) else None
        except json.JSONDecodeError:
            return None


def ollama_up() -> bool:
    try:
        r = httpx.get(f"{OLLAMA_HOST}/api/tags", timeout=2.0)
        return r.status_code == 200
    except Exception:
        return False


def backends() -> dict[str, Any]:
    groq = groq_key_present()
    ollama = ollama_up()
    if groq:
        active = "groq"
        model = GROQ_MODEL
    elif ollama:
        active = "ollama"
        model = OLLAMA_MODEL
    else:
        active = "none"
        model = None
    return {
        "groq": groq,
        "ollama": ollama,
        "active": active,
        "model": model,
    }


def _complete_groq(system: str, user: str) -> str:
    from groq import Groq

    import os

    client = Groq(api_key=os.environ["GROQ_API_KEY"].strip(), timeout=LLM_TIMEOUT)
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return (resp.choices[0].message.content or "").strip()


def _complete_ollama(system: str, user: str) -> str:
    r = httpx.post(
        f"{OLLAMA_HOST}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.2},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        },
        timeout=LLM_TIMEOUT,
    )
    r.raise_for_status()
    data = r.json()
    return str((data.get("message") or {}).get("content") or "").strip()


def complete_json(system: str, user: str) -> tuple[dict[str, Any] | None, str, str | None]:
    """Returns (obj, backend, error)."""
    info = backends()
    active = info["active"]
    if active == "none":
        return None, "none", "no LLM backend (set GROQ_API_KEY or start Ollama)"
    try:
        if active == "groq":
            raw = _complete_groq(system, user)
        else:
            raw = _complete_ollama(system, user)
    except Exception as exc:
        return None, active, f"{type(exc).__name__}: {exc}"
    obj = _extract_json(raw)
    if obj is None:
        return None, active, "LLM did not return JSON"
    return obj, active, None


def validate_llm(obj: dict[str, Any]) -> dict[str, Any] | None:
    dept = str(obj.get("department", "")).strip()
    urg = str(obj.get("urgency", "")).strip().upper()
    lang = str(obj.get("language", "")).strip().lower()
    if dept not in DEPARTMENTS or urg not in URGENCY:
        return None
    if lang not in LANGUAGES:
        lang = "en"
    try:
        dconf = float(obj.get("department_confidence", 0.7))
        uconf = float(obj.get("urgency_confidence", 0.7))
    except (TypeError, ValueError):
        dconf, uconf = 0.7, 0.7
    dconf = max(0.0, min(1.0, dconf))
    uconf = max(0.0, min(1.0, uconf))
    reply = str(obj.get("suggested_reply") or "").strip()
    if not reply:
        return None
    needs = obj.get("needs_human")
    if not isinstance(needs, bool):
        needs = min(dconf, uconf) < 0.55
    return {
        "language": lang,
        "department": dept,
        "urgency": urg,
        "department_confidence": round(dconf, 3),
        "urgency_confidence": round(uconf, 3),
        "needs_human": needs,
        "suggested_reply": reply,
        "rationale": str(obj.get("rationale") or "").strip(),
    }


def llm_triage(text: str, sklearn_hint: dict[str, Any] | None = None) -> dict[str, Any]:
    hint = ""
    if sklearn_hint:
        hint = (
            f"\nLocal classifier hint (may be wrong): "
            f"dept={sklearn_hint.get('department')} "
            f"({sklearn_hint.get('department_confidence')}), "
            f"urgency={sklearn_hint.get('urgency')} "
            f"({sklearn_hint.get('urgency_confidence')}), "
            f"lang={sklearn_hint.get('language')}."
        )
    user = (
        "Departments (use exact strings):\n- "
        + "\n- ".join(DEPARTMENTS)
        + "\n\nTicket:\n"
        + text.strip()
        + hint
    )
    obj, backend, err = complete_json(SYSTEM, user)
    out: dict[str, Any] = {"backend": backend, "error": err, "used": False}
    if obj is None:
        return out
    parsed = validate_llm(obj)
    if parsed is None:
        out["error"] = err or "LLM JSON failed validation"
        return out
    parsed["backend"] = backend
    parsed["error"] = None
    parsed["used"] = True
    return parsed
