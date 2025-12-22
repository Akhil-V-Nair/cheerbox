# pipeline/transform/character_anchor_validator.py

ALLOWED_TYPES = {
    "protagonist",
    "antagonist",
    "duo",
    "team",
    "symbolic"
}

ABSTRACT_WORDS = {
    "identity",
    "journey",
    "emotional",
    "existential",
    "psychological",
    "fractured"
}

def validate_character_anchors(anchors):
    valid = []

    for a in anchors:
        if not isinstance(a, dict):
            continue

        label = a.get("label", "").strip()
        desc = a.get("descriptor", "").strip()
        atype = a.get("type")

        if not label or not desc:
            continue

        if atype not in ALLOWED_TYPES:
            continue

        if any(w in desc.lower() for w in ABSTRACT_WORDS):
            continue

        valid.append({
            "label": label,
            "descriptor": desc,
            "type": atype
        })

    return valid
