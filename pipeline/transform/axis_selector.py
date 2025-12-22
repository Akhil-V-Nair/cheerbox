# pipeline/transform/axis_selector.py

from collections import defaultdict
from .axis_rules import GENRE_AXIS_RULES
from .axis_keywords import AXIS_KEYWORDS


def select_axes(genres, premise, character_anchors, max_axes=3):
    """
    Deterministically select axes based on genre + keyword overlap.
    """

    candidate_axes = set()
    for g in genres:
        name = g["name"] if isinstance(g, dict) else str(g)
        if name in GENRE_AXIS_RULES:
            candidate_axes.update(GENRE_AXIS_RULES[name])

    text = premise.lower()
    for c in character_anchors:
        text += " " + c["label"].lower()

    scores = defaultdict(int)

    for axis in candidate_axes:
        for kw in AXIS_KEYWORDS.get(axis, []):
            if kw in text:
                scores[axis] += 1

    # sort by score desc, fallback to genre priority
    sorted_axes = sorted(
        candidate_axes,
        key=lambda a: scores[a],
        reverse=True
    )

    return sorted_axes[:max_axes]
