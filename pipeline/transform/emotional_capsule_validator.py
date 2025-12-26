# pipeline/transform/emotional_capsule_validator.py

import re

def validate_emotional_capsules(capsules, axes):
    if not capsules:
        return False, "no_capsules"

    if len(capsules) < 4:
        return False, "too_few_capsules"

    for c in capsules:
        if "axis" not in c or "emotion" not in c or "text" not in c:
            return False, "invalid_structure"

        if c["axis"] not in axes:
            return False, "invalid_axis"

        if len(c["text"].split()) > 20:
            return False, "text_too_long"

        # Light AI-language guard
        if re.search(r"\b(masterfully|intricately|explores|delves)\b", c["text"].lower()):
            return False, "ai_language"

    return True, "pass"
