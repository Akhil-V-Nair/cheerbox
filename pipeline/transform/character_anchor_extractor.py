# pipeline/transform/character_anchor_extractor.py

import json

def extract_character_anchors(client, title: str, premise: str):
    prompt = f"""
Extract CHARACTER ANCHORS for a movie.

Definition:
A character anchor is a SIMPLE, CONCRETE identifier
that instantly helps a human recognize the movie.

Rules:
- 1 to 3 anchors ONLY
- Use REAL character names or team names
- NO emotions
- NO themes
- NO abstract language
- NO metaphor

Allowed types:
- protagonist
- antagonist
- duo
- team
- symbolic

Return ONLY valid JSON.
No markdown. No explanation.

Format:
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

    resp = client.responses.create(
        model="gpt-4o-mini",
        input=prompt
    )

    raw = resp.output_text.strip()

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
        return []
    except json.JSONDecodeError:
        print(f"[!] JSON parse failed for: {title}")
        print(raw)
        return []
