def generate_emotional_capsules(client, title, premise, axes):
    """
    Returns RAW TEXT from the LLM.
    JSON is encouraged but NOT required.
    """

    axes_text = "\n".join(f"- {a}" for a in axes)

    prompt = f"""
Generate 5 emotional capsules for this film.

Each capsule must include:
- axis: choose one axis from the list below
- emotion: one simple human word
- text: one short sentence describing an emotional tension

Rules:
- Do NOT use second-person language.
- Do NOT mention characters or names.
- Do NOT describe specific scenes.
- Do NOT explain the movie.
- Avoid academic or critic language.
- Language must sound casual and human.

Axes:
{axes_text}

Film premise:
{premise}

Return JSON if possible.
If not, return one capsule per line in this format:
AXIS | emotion | text
"""

    resp = client.responses.create(
        model="gpt-4o-mini",
        input=prompt
    )

    return resp.output_text.strip()
