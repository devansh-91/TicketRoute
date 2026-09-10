import re

DEVANAGARI = re.compile(r"[\u0900-\u097F]")

HINGLISH_LEXICON = {
    "nahi", "nahin", "nai", "nhi", "mera", "meri", "mere", "hai", "hain",
    "kya", "kyun", "kyu", "kaise", "kab", "abhi", "paise", "paisa",
    "kat", "kata", "gaya", "gayi", "gaye", "krdo", "karo", "bhai", "yaar",
    "band", "hogaya", "kyunki", "lekin", "magar", "toh", "tha", "thi",
    "raha", "rahi", "mujhe", "mujhko", "unka", "uska", "yeh", "woh",
    "kripya", "dhanyavad", "shukriya", "jaldi", "bahut", "galat",
    "samjhao", "dikha", "raha", "hoon", "karo", "sakte",
}


def detect_language(text: str) -> str:
    if not text or not str(text).strip():
        return "en"
    t = str(text)
    if DEVANAGARI.search(t):
        return "hi"
    tokens = re.findall(r"[a-zA-Z']+", t.lower())
    if not tokens:
        return "en"
    hits = sum(1 for tok in tokens if tok in HINGLISH_LEXICON)
    # romanised Hindi / code-mix
    if hits >= 2 or (hits == 1 and len(tokens) <= 8):
        return "hinglish"
    return "en"
