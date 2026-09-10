"""Synthetic multilingual tickets for TicketRoute (reproducible)."""

from __future__ import annotations

import csv
import random
from pathlib import Path

from ticketroute.language import detect_language
from ticketroute.taxonomy import DEPARTMENTS, URGENCY

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "tickets.csv"

# (department, urgency, lang, text)
TEMPLATES: list[tuple[str, str, str, str]] = [
    # Billing EN
    ("Billing & Payments", "P1", "en", "Payment was deducted twice for invoice {n} and my account still shows overdue."),
    ("Billing & Payments", "P1", "en", "Charged {amt} but the service is completely down. Need an immediate refund."),
    ("Billing & Payments", "P2", "en", "UPI payment failed yet {amt} left my bank. Transaction id TXN{n}."),
    ("Billing & Payments", "P2", "en", "I cannot pay my bill. Card is declined every time I try checkout."),
    ("Billing & Payments", "P3", "en", "Please explain the extra {amt} convenience fee on last month's invoice."),
    ("Billing & Payments", "P3", "en", "How do I download GST invoice for order {n}?"),
    ("Billing & Payments", "P4", "en", "Thanks, the refund for invoice {n} arrived. Just confirming."),
    ("Billing & Payments", "P4", "en", "FYI I updated my billing address. No issue otherwise."),
    # Billing HI
    ("Billing & Payments", "P1", "hi", "मेरे खाते से {amt} दो बार कट गया और सेवा अभी भी बंद है। तुरंत रिफंड चाहिए।"),
    ("Billing & Payments", "P2", "hi", "बिल भरने पर पेमेंट फेल हो गया लेकिन पैसे कट गए। TXN{n} चेक करें।"),
    ("Billing & Payments", "P3", "hi", "पिछले बिल में अतिरिक्त शुल्क {amt} क्यों लगाया गया?"),
    ("Billing & Payments", "P4", "hi", "रिफंड मिल गया, धन्यवाद। कोई और समस्या नहीं है।"),
    # Billing Hinglish
    ("Billing & Payments", "P1", "hinglish", "Mera payment do baar kat gaya hai aur service abhi bhi down hai, jaldi refund do."),
    ("Billing & Payments", "P2", "hinglish", "UPI fail hua lekin paise nahi aaye wapas, TXN{n} check karo."),
    ("Billing & Payments", "P3", "hinglish", "Last bill me extra {amt} kyun add kiya, samjhao."),
    ("Billing & Payments", "P4", "hinglish", "Refund aa gaya bhai, shukriya. Bas confirm kar raha hoon."),
    # Account
    ("Account / KYC / Login", "P1", "en", "Someone else logged into my account. Please freeze it now."),
    ("Account / KYC / Login", "P1", "en", "I did not request this password reset. Possible account takeover."),
    ("Account / KYC / Login", "P2", "en", "Cannot login after KYC update. OTP never arrives."),
    ("Account / KYC / Login", "P2", "en", "PAN upload keeps failing and I am locked out of the dashboard."),
    ("Account / KYC / Login", "P3", "en", "How do I change the registered mobile number on my profile?"),
    ("Account / KYC / Login", "P4", "en", "KYC approved, thanks for the quick help."),
    ("Account / KYC / Login", "P1", "hi", "मेरे अकाउंट में कोई और लॉगिन कर रहा है। तुरंत बंद करें।"),
    ("Account / KYC / Login", "P2", "hi", "लॉगिन नहीं हो रहा, OTP नहीं आ रहा है।"),
    ("Account / KYC / Login", "P3", "hi", "प्रोफाइल पर मोबाइल नंबर कैसे बदलें?"),
    ("Account / KYC / Login", "P1", "hinglish", "Kisi aur ne mera account hack kar liya hai, turant band karo."),
    ("Account / KYC / Login", "P2", "hinglish", "Login nahi ho raha, OTP nahi aa raha hai."),
    ("Account / KYC / Login", "P3", "hinglish", "Registered number kaise change karein profile me?"),
    # Technical
    ("Technical / App crash", "P1", "en", "App crashes on launch since the last update. Completely unusable."),
    ("Technical / App crash", "P2", "en", "Checkout page spins forever on Android 14. Order cannot be placed."),
    ("Technical / App crash", "P3", "en", "Dark mode contrast is too low on the settings screen."),
    ("Technical / App crash", "P4", "en", "The new search is nicer. Small suggestion: remember last filter."),
    ("Technical / App crash", "P1", "hi", "ऐप खुलते ही क्रैश हो जाती है। बिल्कुल काम नहीं कर रही।"),
    ("Technical / App crash", "P2", "hi", "पेमेंट स्क्रीन पर ऐप हैंग हो जाती है।"),
    ("Technical / App crash", "P1", "hinglish", "App open karte hi crash ho rahi hai, kuch kaam nahi ho raha."),
    ("Technical / App crash", "P2", "hinglish", "Checkout pe app hang ho jati hai Android pe."),
    ("Technical / App crash", "P3", "hinglish", "Settings page slow hai, 5 second lagata hai load hone me."),
    # Order
    ("Product / Order / Delivery", "P1", "en", "Paid order {n} marked delivered but nothing arrived. This is urgent."),
    ("Product / Order / Delivery", "P2", "en", "Order {n} is 4 days late. Tracking has not moved."),
    ("Product / Order / Delivery", "P3", "en", "Can I change the delivery slot for order {n} to Saturday?"),
    ("Product / Order / Delivery", "P4", "en", "Order {n} arrived in good condition. Thank you."),
    ("Product / Order / Delivery", "P1", "hi", "ऑर्डर {n} डिलीवर्ड दिखाया गया लेकिन सामान नहीं आया। पैसे कट चुके हैं।"),
    ("Product / Order / Delivery", "P2", "hi", "ऑर्डर {n} चार दिन से अटका हुआ है।"),
    ("Product / Order / Delivery", "P1", "hinglish", "Order {n} delivered dikha raha hai lekin saman nahi aaya, payment kat gaya."),
    ("Product / Order / Delivery", "P2", "hinglish", "Mera order nahi aaya, tracking 4 din se same hai."),
    ("Product / Order / Delivery", "P3", "hinglish", "Delivery slot Saturday kar sakte ho kya order {n} ka?"),
    # Fraud
    ("Abuse / Safety / Fraud", "P1", "en", "Phishing SMS used your brand. They asked for OTP. Please investigate."),
    ("Abuse / Safety / Fraud", "P1", "en", "A user threatened me in chat and shared my address. Unsafe."),
    ("Abuse / Safety / Fraud", "P2", "en", "Seller listing looks fake. They asked me to pay off-app."),
    ("Abuse / Safety / Fraud", "P3", "en", "I want to report spam messages in the in-app inbox."),
    ("Abuse / Safety / Fraud", "P1", "hi", "फेक कॉल आ रही है, OTP मांग रहे हैं आपके नाम से। धोखाधड़ी है।"),
    ("Abuse / Safety / Fraud", "P2", "hi", "सेलर ऐप के बाहर पेमेंट मांग रहा है। फ्रॉड लग रहा है।"),
    ("Abuse / Safety / Fraud", "P1", "hinglish", "Fake call aa rahi hai OTP mang rahe hain, yeh fraud hai jaldi dekho."),
    ("Abuse / Safety / Fraud", "P2", "hinglish", "Seller off-app payment maang raha hai, scam lag raha hai."),
    # Feedback
    ("Feedback / General", "P4", "en", "Love the new dashboard. Keep it up."),
    ("Feedback / General", "P3", "en", "Could you add Hindi language to the help centre articles?"),
    ("Feedback / General", "P4", "en", "Just saying thanks to the support agent who helped yesterday."),
    ("Feedback / General", "P4", "hi", "नया डैशबोर्ड अच्छा लगा। धन्यवाद।"),
    ("Feedback / General", "P3", "hi", "हेल्प सेंटर में हिंदी लेख जोड़िए।"),
    ("Feedback / General", "P4", "hinglish", "Naya dashboard bahut accha hai, shukriya."),
    ("Feedback / General", "P3", "hinglish", "Help centre me Hindi articles add karo please."),
]

VARIANTS = {
    "en": [
        " Please help.",
        " Need update today.",
        " Ticket for order follow-up.",
        " Customer id C{n}.",
        " Raised via app chat.",
        " waiting since morning.",
        "",
        "",
    ],
    "hi": [
        " यह बहुत जरूरी है।",
        " कृपया जल्दी जवाब दें।",
        " ग्राहक आईडी C{n}।",
        "",
        "",
    ],
    "hinglish": [
        " kripya jaldi reply do.",
        " bahut zaruri hai bhai.",
        " customer id C{n}.",
        "",
        "",
    ],
}


def generate(n: int = 1200, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    rows = []
    for i in range(n):
        dept, urg, lang, tmpl = rng.choice(TEMPLATES)
        num = rng.randint(10000, 99999)
        amt = rng.choice(["₹499", "₹1,299", "₹2,050", "₹89"])
        text = tmpl.format(n=num, amt=amt) + rng.choice(VARIANTS[lang]).format(n=num)
        if rng.random() < 0.08:
            # light noise
            text = text + " " + rng.choice(["??", "!!!", "pls", "urgent", "ok"])
        rows.append(
            {
                "id": f"T{i+1:04d}",
                "text": text.strip(),
                "department": dept,
                "urgency": urg,
                "language": lang,
                "channel": rng.choice(["app", "email", "web", "whatsapp"]),
                "timestamp": f"2026-09-{(i % 28) + 1:02d}T10:00:00+05:30",
            }
        )
    return rows


def write_csv(path: Path | None = None, n: int = 1200) -> Path:
    path = path or DATA
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = generate(n=n)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["id", "text", "department", "urgency", "language", "channel", "timestamp"],
        )
        w.writeheader()
        w.writerows(rows)
    # sanity: language detector vs intended (Hinglish/hi/en templates are tagged)
    return path


if __name__ == "__main__":
    p = write_csv()
    print("wrote", p, "rows", 1200)
    # quick lang overlap check
    from collections import Counter

    rows = generate(200)
    c = Counter()
    for r in rows:
        pred = detect_language(r["text"])
        c[(r["language"], pred)] += 1
    print("lang gold->pred counts (sample 200):")
    for k, v in sorted(c.items()):
        print(k, v)
