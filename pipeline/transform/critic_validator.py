import re

MIN_WORDS = 70
MAX_WORDS = 130

FORBIDDEN_GENERIC_PHRASES = [
    "human condition",
    "deeper themes",
    "complex narrative",
    "emotional journey",
    "thought-provoking",
    "layered storytelling"
]

def validate_critic_summary(text: str) -> tuple[bool, str]:
    """
    Returns (is_valid, reason)
    """

    if not text or not text.strip():
        return False, "empty"

    words = text.split()
    wc = len(words)

    if wc < MIN_WORDS:
        return False, "too_short"

    if wc > MAX_WORDS:
        return False, "too_long"

    lower = text.lower()

    for phrase in FORBIDDEN_GENERIC_PHRASES:
        if phrase in lower:
            return False, f"generic_phrase:{phrase}"

    # reject bullet points, lists, formatting
    if re.search(r"[\n•\-]", text):
        return False, "formatting_detected"

    return True, "pass"
