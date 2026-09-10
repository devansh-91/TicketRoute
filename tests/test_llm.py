from ticketroute.llm import _extract_json, validate_llm


def test_extract_plain_json():
    obj = _extract_json('{"department": "Billing & Payments", "urgency": "P2"}')
    assert obj["urgency"] == "P2"


def test_extract_fenced_json():
    raw = '```json\n{"department": "x"}\n```'
    assert _extract_json(raw)["department"] == "x"


def test_validate_rejects_bad_dept():
    assert validate_llm({"department": "Sales", "urgency": "P1", "language": "en", "suggested_reply": "hi"}) is None


def test_validate_ok():
    out = validate_llm(
        {
            "department": "Billing & Payments",
            "urgency": "p2",
            "language": "hinglish",
            "department_confidence": 0.9,
            "urgency_confidence": 0.8,
            "needs_human": False,
            "suggested_reply": "Aapka payment check ho raha hai.",
            "rationale": "payment words",
        }
    )
    assert out is not None
    assert out["urgency"] == "P2"
    assert out["language"] == "hinglish"
    assert "payment" in out["suggested_reply"].lower() or "payment" in out["suggested_reply"]
