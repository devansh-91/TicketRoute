import re
import unicodedata


def normalize(text: str) -> str:
    if text is None:
        return ""
    t = unicodedata.normalize("NFC", str(text))
    t = t.replace("\u00a0", " ")
    t = re.sub(r"https?://\S+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t
