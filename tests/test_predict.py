from ticketroute.predict import predict_ticket
from ticketroute.taxonomy import ABSTAIN_DEPARTMENT, SLA_HOURS


def test_local_hinglish_order():
    p = predict_ticket("Mera order nahi aaya, payment kat gaya.", use_llm=False, persist=False)
    assert p["language"] == "hinglish"
    assert p["department"] == "Product / Order / Delivery"
    assert p["source"] == "sklearn"
    assert p["suggested_reply"]
    assert p["sla_hours"] == SLA_HOURS[p["urgency"]]
    assert p["similar"]


def test_local_fraud():
    p = predict_ticket(
        "Phishing SMS used your brand. They asked for OTP.",
        use_llm=False,
        persist=False,
    )
    assert p["language"] == "en"
    assert p["department"] == "Abuse / Safety / Fraud"
    assert p["urgency"] == "P1"


def test_other_language_needs_human():
    p = predict_ticket("என் ஆர்டர் வரவில்லை", use_llm=False, persist=False)
    assert p["language"] == "other"
    assert p["needs_human"] is True
