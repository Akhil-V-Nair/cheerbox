# pipeline/transform/character_anchor_extractor.py

def extract_character_anchors(client, title: str, premise: str):
    """
    Generates 1–3 character anchors that help humans
    instantly recognize the movie.
    """

    prompt = f"""
You are extracting CHARACTER ANCHORS for a movie.

A character anchor is a SIMPLE, HUMAN-RECOGNIZABLE HANDLE
that lets someone instantly identify the movie.

Rules:
- Return 1 to 3 anchors ONLY
- Use REAL character names or team names
- Keep descriptors literal and short
- NO emotions
- NO themes
- NO abstract language

Allowed types:
- protagonist
- antagonist
- duo
- team
- symbolic

Return STRICT JSON ARRAY ONLY.
No markdown. No explanation.

Example:
[
  {{
    "label": "Cooper",
    "descriptor": "astronaut father",
    "type": "protagonist"
  }}
]

Movie title: {title}
Premise: {premise}
"""

    response = client.responses.create(
        model="gpt-4o-mini",
        input=prompt
    )

    try:
        return response.output_parsed
    except Exception:
        return []
