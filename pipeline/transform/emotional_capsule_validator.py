import re

SECOND_PERSON = re.compile(r"\b(you|your|you're|you’re)\b", re.I)

def validate_emotional_capsules(capsules, axes):
    """
    capsules: list[dict]
    """

    if not isinstance(capsules, list):
        return False, "not_list"

    if len(capsules) < 4:
        return False, "too_few_capsules"

    for c in capsules:
        if c.get("axis") not in axes:
            return False, "invalid_axis"

        text = c.get("text", "")
        if not text or len(text.split()) > 25:
            return False, "bad_text_length"

        if SECOND_PERSON.search(text):
            return False, "second_person"

    return True, "pass"
