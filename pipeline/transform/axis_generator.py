#!/usr/bin/env python3

from typing import List, Dict
from openai import OpenAI

GENRE_AXIS_RULES = {
    "Science Fiction": [
        "Reality ↔ Illusion",
        "Control ↔ Surrender",
        "Power ↔ Responsibility",
        "Purpose ↔ Emptiness",
        "Freedom ↔ Constraint",
    ],
    "Action": [
        "Safety ↔ Threat",
        "Order ↔ Chaos",
        "Individual ↔ Collective",
        "Survival ↔ Sacrifice",
    ],
    "Fantasy": [
        "Power ↔ Responsibility",
        "Identity ↔ Role",
        "Order ↔ Chaos",
        "Loyalty ↔ Betrayal",
    ],
    "Drama": [
        "Identity ↔ Role",
        "Purpose ↔ Emptiness",
        "Justice ↔ Compromise",
        "Loyalty ↔ Betrayal",
    ],
    "Adventure": [
        "Individual ↔ Collective",
        "Freedom ↔ Constraint",
        "Survival ↔ Sacrifice",
    ],
}

def _allowed_axes(genres: List[str]) -> List[str]:
    axes = set()
    for g in genres:
        axes.update(GENRE_AXIS_RULES.get(g, []))
    return list(axes)

def generate_axes(
    client: OpenAI,
    title: str,
    premise: str,
    genres: List[str]
) -> Dict:
    allowed = _allowed_axes(genres)
    if not allowed:
        return {"primary": [], "secondary": None, "status": "no_genre_axes"}

    prompt = f"""
Select emotional tension axes for this movie.

Movie: {title}
Premise: {premise}

Allowed axes:
{", ".join(allowed)}

Rules:
- Choose EXACTLY 2 primary axes
- Choose EXACTLY 1 secondary axis
- Use ONLY from allowed list
- No explanations

Format:
Primary:
- axis
- axis
Secondary:
- axis
"""

    resp = client.responses.create(
        model="gpt-4o-mini",
        input=prompt
    )

    text = resp.output_text or ""

    primary, secondary = [], None
    for line in text.splitlines():
        line = line.strip().lstrip("- ").strip()
        if line in allowed:
            if len(primary) < 2:
                primary.append(line)
            elif secondary is None and line not in primary:
                secondary = line

    return {
        "primary": primary[:2],
        "secondary": secondary,
        "status": "pass" if primary else "flagged",
    }
