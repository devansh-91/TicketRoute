import re

DEVANAGARI = re.compile(r"[\u0900-\u097F]")
# Tamil, Telugu, Kannada, Malayalam, Gujarati, Bengali, Gurmukhi, Oriya
OTHER_INDIC = re.compile(
    r"[\u0B80-\u0BFF\u0C00-\u0C7F\u0C80-\u0CFF\u0D00-\u0D7F"
    r"\u0A80-\u0AFF\u0980-\u09FF\u0A00-\u0A7F\u0B00-\u0B7F]"
)

HINGLISH_LEXICON = {
    "nahi", "nahin", "nai", "nhi", "mera", "meri", "mere", "hai", "hain",
    "kya", "kyun", "kyu", "kaise", "kab", "abhi", "paise", "paisa",
    "kat", "kata", "gaya", "gayi", "gaye", "krdo", "karo", "bhai", "yaar",
    "band", "hogaya", "kyunki", "lekin", "magar", "toh", "tha", "thi",
    "raha", "rahi", "mujhe", "mujhko", "unka", "uska", "yeh", "woh",
    "kripya", "dhanyavad", "shukriya", "jaldi", "bahut", "galat",
    "samjhao", "dikha", "hoon", "sakte", "aap", "aapke", "naya",
}


def detect_language(text: str) -> str:
    if not text or not str(text).strip():
        return "other"
    t = str(text)
    if OTHER_INDIC.search(t) and not DEVANAGARI.search(t):
        return "other"
    if DEVANAGARI.search(t):
        return "hi"
    tokens = re.findall(r"[a-zA-Z']+", t.lower())
    if not tokens:
        return "other"
    hits = sum(1 for tok in tokens if tok in HINGLISH_LEXICON)
    if hits >= 2 or (hits == 1 and len(tokens) <= 8):
        return "hinglish"
    # mostly latin letters
    letters = sum(ch.isalpha() for ch in t)
    latin = sum("a" <= ch.lower() <= "z" for ch in t)
    if letters and latin / max(letters, 1) < 0.5:
        return "other"
    return "en"
