# cheerbox/pipeline/transform/critic_validator.py

import re

BANNED_WORDS = {
    "masterfully",
    "intricately",
    "explores",
    "examines",
    "delves",
    "narrative",
    "cinematography",
    "themes",
    "symbolizes"
}

def validate_critic_summary(text: str) -> tuple[bool, str]:
    """
    Validates whether the critic summary sounds human and experiential.
    """

    if not text or len(text.split()) < 60:
        return False, "too_short"

    lowered = text.lower()

    for word in BANNED_WORDS:
        if word in lowered:
            return False, f"banned_word:{word}"

    # must reference audience experience
    if not any(
        phrase in lowered
        for phrase in ["viewers", "audience", "people", "you feel", "it feels"]
    ):
        return False, "no_audience_perspective"

    # reject academic tone
    if re.search(r"\b(identity|tension|duality|conflict)\b", lowered):
        return False, "abstract_language"

    return True, "pass"
