from ticketroute.llm import _extract_json
from ticketroute.language import detect_language
from ticketroute.reply import draft_reply
from ticketroute.taxonomy import DEPARTMENTS


def test_extract_plain_json():
    obj = _extract_json('{"suggested_reply": "ok", "rationale": "x"}')
    assert obj["suggested_reply"] == "ok"


def test_extract_fenced_json():
    raw = '```json\n{"suggested_reply": "x"}\n```'
    assert _extract_json(raw)["suggested_reply"] == "x"


def test_devanagari_is_hi():
    assert detect_language("मेरा बिल गलत है") == "hi"


def test_hinglish():
    assert detect_language("Mera order nahi aaya, payment kat gaya") == "hinglish"


def test_english():
    assert detect_language("Payment was deducted twice for invoice 12345") == "en"


def test_tamil_is_other():
    assert detect_language("என் ஆர்டர் வரவில்லை") == "other"


def test_reply_contains_dept():
    r = draft_reply("Billing & Payments", "P2", "en")
    assert "Billing" in r
    assert "P2" in r
    assert "4" in r  # SLA hours


def test_departments_include_abstain():
    assert "Other / Unknown" in DEPARTMENTS
    assert len(DEPARTMENTS) == 7
