from ticketroute.predict import predict_ticket


def test_local_hinglish_order():
    p = predict_ticket("Mera order nahi aaya, payment kat gaya.", use_llm=False)
    assert p["language"] == "hinglish"
    assert p["department"] == "Product / Order / Delivery"
    assert p["source"] == "sklearn"
    assert p["suggested_reply"]
    assert p["similar"]


def test_local_fraud():
    p = predict_ticket("Phishing SMS used your brand. They asked for OTP.", use_llm=False)
    assert p["language"] == "en"
    assert p["department"] == "Abuse / Safety / Fraud"
    assert p["urgency"] == "P1"
