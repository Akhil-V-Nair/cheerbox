# pipeline/transform/axis_extractor.py

from typing import List, Dict
from openai import OpenAI
from pipeline.transform.axis_ontology import AXIS_FAMILIES, AXIS_TO_FAMILY

def extract_movie_axes(
    client: OpenAI,
    title: str,
    premise: str,
    genres: List[str],
    character_anchors: List[str],
    max_primary: int = 2,
    allow_secondary: bool = True
) -> Dict:
    """
    Returns:
    {
      "primary_axes": [...],
      "secondary_axis": str | None
    }
    """

    # Build candidate pool (flattened)
    candidate_axes = sorted({axis for axes in AXIS_FAMILIES.values() for axis in axes})

    prompt = f"""
You are selecting emotional tension axes for a movie.

Movie title:
{title}

Premise (short identifier):
{premise}

Characters / anchors:
{", ".join(character_anchors) if character_anchors else "None"}

Rules:
- Choose AT MOST {max_primary} primary axes
- Optionally choose 1 secondary axis
- Axes must be chosen ONLY from the list below
- Do NOT invent new axes
- Do NOT choose two axes from the same family
- If none strongly apply, return empty lists

Allowed axes:
{chr(10).join(candidate_axes)}

Respond strictly in JSON:
{{
  "primary_axes": [],
  "secondary_axis": null
}}
"""

    resp = client.responses.create(
        model="gpt-4o-mini",
        input=prompt
    )

    data = resp.output_parsed or {}

    primary = data.get("primary_axes", []) or []
    secondary = data.get("secondary_axis")

    # ---------- Post-validation ----------
    used_families = set()
    cleaned_primary = []

    for axis in primary:
        family = AXIS_TO_FAMILY.get(axis)
        if family and family not in used_families:
            cleaned_primary.append(axis)
            used_families.add(family)

    cleaned_secondary = None
    if secondary:
        fam = AXIS_TO_FAMILY.get(secondary)
        if fam and fam not in used_families:
            cleaned_secondary = secondary

    return {
        "primary_axes": cleaned_primary[:max_primary],
        "secondary_axis": cleaned_secondary
    }
