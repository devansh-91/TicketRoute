"""Load taxonomy from config/taxonomy.yaml with a safe in-code fallback."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
YAML_PATH = ROOT / "config" / "taxonomy.yaml"

_FALLBACK = {
    "departments": [
        "Billing & Payments",
        "Account / KYC / Login",
        "Technical / App crash",
        "Product / Order / Delivery",
        "Abuse / Safety / Fraud",
        "Feedback / General",
        "Other / Unknown",
    ],
    "abstain_department": "Other / Unknown",
    "abstain_threshold": 0.45,
    "urgency": {
        "P1": {"label": "Critical", "sla_hours": 1},
        "P2": {"label": "High", "sla_hours": 4},
        "P3": {"label": "Normal", "sla_hours": 24},
        "P4": {"label": "Low", "sla_hours": 72},
    },
    "languages": ["en", "hi", "hinglish", "other"],
    "channels": ["app", "email", "web", "whatsapp", "phone"],
}


def _load() -> dict:
    if YAML_PATH.exists():
        try:
            import yaml

            data = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8")) or {}
            merged = dict(_FALLBACK)
            merged.update(data)
            return merged
        except Exception:
            return dict(_FALLBACK)
    return dict(_FALLBACK)


CFG = _load()
DEPARTMENTS: list[str] = list(CFG["departments"])
ROUTEABLE = [d for d in DEPARTMENTS if d != CFG["abstain_department"]]
ABSTAIN_DEPARTMENT: str = str(CFG["abstain_department"])
ABSTAIN_THRESHOLD: float = float(CFG["abstain_threshold"])
URGENCY: list[str] = list(CFG["urgency"].keys())
URGENCY_LABEL = {k: v["label"] for k, v in CFG["urgency"].items()}
SLA_HOURS = {k: int(v["sla_hours"]) for k, v in CFG["urgency"].items()}
LANGUAGES: list[str] = list(CFG["languages"])
CHANNELS: list[str] = list(CFG["channels"])
