"""Groq (preferred) or Ollama — reply polish only (labels stay local)."""
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
from ticketroute.taxonomy import SLA_HOURS

SYSTEM = """You rewrite a first-reply for an Indian support desk.
Return ONLY JSON: {"suggested_reply": "...", "rationale": "one sentence"}
Rules:
- Keep the same language as the ticket (en, hi, or hinglish).
- You MUST keep the SLA hours number exactly as given. Do not invent 24h if SLA is 1.
- Do not change department or urgency.
- Do not invent refunds, amounts, legal conclusions, or that an account was already frozen.
- Be specific to the ticket text. Short: 2-4 sentences.
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
        active, model = "groq", GROQ_MODEL
    elif ollama:
        active, model = "ollama", OLLAMA_MODEL
    else:
        active, model = "none", None
    return {"groq": groq, "ollama": ollama, "active": active, "model": model}


def _complete_groq(system: str, user: str) -> str:
    import os
    from groq import Groq

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
    info = backends()
    active = info["active"]
    if active == "none":
        return None, "none", "no LLM backend"
    try:
        raw = _complete_groq(system, user) if active == "groq" else _complete_ollama(system, user)
    except Exception as exc:
        return None, active, f"{type(exc).__name__}: {exc}"
    obj = _extract_json(raw)
    if obj is None:
        return None, active, "LLM did not return JSON"
    return obj, active, None


def llm_polish(
    ticket: str,
    language: str,
    department: str,
    urgency: str,
    template_reply: str,
) -> dict[str, Any]:
    sla = SLA_HOURS.get(urgency, 24)
    user = (
        f"language={language}\ndepartment={department}\nurgency={urgency}\n"
        f"SLA_HOURS={sla}\n\nTicket:\n{ticket.strip()}\n\nTemplate (keep SLA {sla}):\n{template_reply}"
    )
    obj, backend, err = complete_json(SYSTEM, user)
    out: dict[str, Any] = {"backend": backend, "error": err, "used": False}
    if not obj:
        return out
    reply = str(obj.get("suggested_reply") or "").strip()
    if not reply:
        out["error"] = err or "empty reply"
        return out
    # refuse if the model dropped the SLA number
    if str(sla) not in reply and f"{sla} " not in reply:
        reply = template_reply
    out.update(
        {
            "used": True,
            "suggested_reply": reply,
            "rationale": str(obj.get("rationale") or "").strip(),
            "error": None,
        }
    )
    return out
