# pipeline/transform/premise_validator.py

import re
from typing import List, Tuple

# --------------------------------------------------
# Genre keyword rules (hard constraints)
# --------------------------------------------------

GENRE_KEYWORDS = {
    "Science Fiction": [
        "space", "alien", "future", "technology", "planet", "ai", "machine"
    ],
    "Action": [
        "fight", "war", "battle", "mission", "threat", "conflict"
    ],
    "Fantasy": [
        "magic", "kingdom", "creature", "curse", "power"
    ],
    "Drama": [
        # drama is allowed to be broader, but still concrete
        "family", "relationship", "life", "choice", "struggle"
    ],
    "Comedy": [
        # no keyword enforcement
    ]
}

# --------------------------------------------------

INVALID_PATTERNS = [
    r"\b(love|identity|meaning|journey|struggle of|explores)\b",
    r"\b(director|actor|hero|villain|team|group)\b",
    r"\b(symbolizes|represents|metaphor)\b"
]

def validate_premise(premise: str, genres: List[dict]) -> Tuple[bool, str]:
    """
    Validates whether a premise is concrete and genre-aligned.
    """

    text = premise.lower()

    # ---- Reject abstraction / meta language ----
    for pattern in INVALID_PATTERNS:
        if re.search(pattern, text):
            return False, "abstract_or_meta_language"

    # ---- Enforce genre keywords ----
    for g in genres:
        genre_name = g.get("name")
        keywords = GENRE_KEYWORDS.get(genre_name)

        if not keywords:
            continue  # genre has no hard constraint

        if not any(k in text for k in keywords):
            return False, f"missing_genre_keyword:{genre_name}"

    # ---- Length sanity ----
    word_count = len(premise.split())
    if word_count < 8 or word_count > 30:
        return False, "invalid_length"

    return True, "pass"
