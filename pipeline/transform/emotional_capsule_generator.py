def generate_emotional_capsules(client, *, title, premise, axes, genre):
    """
    Generates exactly 4 emotional capsules.
    """

    axes_text = "\n".join(f"- {a}" for a in axes)

    prompt = f"""
You describe how a movie FEELS to watch.

You are NOT explaining themes.
You are NOT analyzing cinema.
You are NOT poetic.

Rules:
- Write exactly 4 capsules
- Each capsule has:
  • axis (must be one of the provided axes)
  • emotion (ONE simple word)
  • text (ONE sentence, conversational)
- No plot events
- No character names
- No film theory words
- No words like: explores, reflects, narrative, journey, masterfully

Movie title: {title}
Premise (identifier, not plot):
{premise}

Genre:
{genre}

Allowed emotional axes:
{axes_text}

Output JSON ONLY in this format:

[
  {{
    "axis": "...",
    "emotion": "...",
    "text": "..."
  }}
]
"""

    response = client.responses.create(
        model="gpt-4o-mini",
        input=prompt
    )

    return response.output_text
