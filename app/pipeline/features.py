from app.pipeline.preprocessing import _PATTERNS


def extract_features(raw_text: str) -> dict[str, float | int | bool]:
    n = len(raw_text)
    return {
        "text_len": n,
        "word_count": len(raw_text.split()),
        "exclamation_count": raw_text.count("!"),
        "question_count": raw_text.count("?"),
        "uppercase_ratio": sum(1 for c in raw_text if c.isupper()) / n if n > 0 else 0.0,
        "has_url": bool(_PATTERNS["url"].search(raw_text)),
        "has_phone": bool(_PATTERNS["phone"].search(raw_text)),
        "has_email": bool(_PATTERNS["email"].search(raw_text)),
    }
