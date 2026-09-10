from ticketroute.language import detect_language
from ticketroute.reply import draft_reply
from ticketroute.taxonomy import DEPARTMENTS


def test_devanagari_is_hi():
    assert detect_language("मेरा बिल गलत है") == "hi"


def test_hinglish():
    assert detect_language("Mera order nahi aaya, payment kat gaya") == "hinglish"


def test_english():
    assert detect_language("Payment was deducted twice for invoice 12345") == "en"


def test_reply_contains_dept():
    r = draft_reply("Billing & Payments", "P2", "en")
    assert "Billing" in r
    assert "P2" in r


def test_departments_nonempty():
    assert len(DEPARTMENTS) == 6
