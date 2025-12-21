# pipeline/transform/character_anchor_validator.py

ALLOWED_TYPES = {
    "protagonist",
    "antagonist",
    "duo",
    "team",
    "symbolic"
}

ABSTRACT_WORDS = {
    "emotional",
    "identity",
    "journey",
    "inner",
    "fractured",
    "psychological",
    "existential"
}

def validate_character_anchors(anchors):
    """
    Validates anchors for structure and human readability.
    """
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

        # Reject abstract / AI-ish descriptors
        desc_lower = desc.lower()
        if any(w in desc_lower for w in ABSTRACT_WORDS):
            continue

        valid.append({
            "label": label,
            "descriptor": desc,
            "type": atype
        })

    return valid
