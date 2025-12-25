# pipeline/transform/critic_soft_validator.py

import re

ABSTRACT_PHRASES = [
    "this film explores",
    "themes of life",
    "human condition",
    "journey of self discovery",
    "explores themes of"
]

def soft_validate_critic(summary: str, premise: str) -> tuple[bool, str]:
    if not summary or not premise:
        return False, "empty"

    words = summary.split()
    if len(words) < 70 or len(words) > 150:
        return False, "length_out_of_bounds"

    summary_l = summary.lower()
    premise_l = premise.lower()

    # Reject pure abstraction
    abstract_hits = sum(1 for p in ABSTRACT_PHRASES if p in summary_l)
    if abstract_hits >= 2:
        return False, "too_abstract"

    # Check grounding: at least 2 meaningful overlaps with premise
    premise_tokens = set(
        w for w in re.findall(r"[a-z]{4,}", premise_l)
        if w not in {"about", "their", "there", "which"}
    )

    summary_tokens = set(
        w for w in re.findall(r"[a-z]{4,}", summary_l)
    )

    overlap = premise_tokens.intersection(summary_tokens)
    if len(overlap) < 2:
        return False, "weak_premise_grounding"

    # Must imply conflict or tension
    conflict_markers = {
        "struggle", "conflict", "threat", "pressure",
        "collapse", "choice", "risk", "cost", "loss"
    }

    if not conflict_markers.intersection(summary_tokens):
        return False, "no_conflict_signal"

    return True, "soft_pass"
