import re

# PII masking patterns — order matters: URL before phone (URLs contain digits)
_PATTERNS: dict[str, re.Pattern] = {
    "url": re.compile(r'https?://\S+|www\.\S+', re.IGNORECASE),
    "phone": re.compile(r'(?:\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}'),
    "email": re.compile(r'[\w.\-]+@[\w.\-]+\.\w{2,}'),
}

_WHITESPACE = re.compile(r'\s+')


def preprocess_text(text: str) -> str:
    if not text:
        return text
    text = text.lower()
    text = _PATTERNS["url"].sub("<URL>", text)
    text = _PATTERNS["phone"].sub("<PHONE>", text)
    text = _PATTERNS["email"].sub("<EMAIL>", text)
    return _WHITESPACE.sub(" ", text).strip()
