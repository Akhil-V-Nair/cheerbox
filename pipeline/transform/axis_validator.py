#!/usr/bin/env python3

from typing import Dict, List
from pipeline.transform.axis_generator import GENRE_AXIS_RULES

def validate_axes(
    axes: Dict,
    genres: List[str]
) -> Dict:
    allowed = set()
    for g in genres:
        allowed.update(GENRE_AXIS_RULES.get(g, []))

    errors = []

    for ax in axes.get("primary", []):
        if ax not in allowed:
            errors.append(f"Invalid primary axis: {ax}")

    sec = axes.get("secondary")
    if sec and sec not in allowed:
        errors.append(f"Invalid secondary axis: {sec}")

    if len(set(axes.get("primary", []))) < len(axes.get("primary", [])):
        errors.append("Duplicate primary axes")

    return {
        "valid": not errors,
        "errors": errors
    }
