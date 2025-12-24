# pipeline/transform/axis_ontology.py

AXIS_FAMILIES = {
    "Reality & Perception": {
        "Reality ↔ Illusion",
        "Truth ↔ Deception",
    },
    "Power & Control": {
        "Power ↔ Responsibility",
        "Control ↔ Chaos",
    },
    "Identity & Self": {
        "Identity ↔ Role",
        "Self ↔ Mask",
    },
    "Survival & Stakes": {
        "Safety ↔ Threat",
        "Survival ↔ Sacrifice",
    },
    "Social Bonds": {
        "Belonging ↔ Isolation",
        "Loyalty ↔ Betrayal",
    },
    "Order & Justice": {
        "Order ↔ Corruption",
        "Justice ↔ Compromise",
    },
    "Knowledge & Fear": {
        "Known ↔ Unknown",
        "Safety ↔ Exposure",
    },
    "Meaning & Absurdity": {
        "Meaning ↔ Absurdity",
    },
}

# Reverse lookup
AXIS_TO_FAMILY = {
    axis: family
    for family, axes in AXIS_FAMILIES.items()
    for axis in axes
}
