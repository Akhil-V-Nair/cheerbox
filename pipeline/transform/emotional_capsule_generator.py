# pipeline/transform/emotional_capsule_generator.py

def generate_emotional_capsules(client, title, premise, axes):
    axes_text = ", ".join(axes)

    prompt = f"""
Write exactly 5 emotional capsules for the movie below.

STRICT FORMAT RULE (DO NOT BREAK):
Each line must follow this format exactly:
AXIS :: emotion :: short sentence

Rules:
- AXIS must be one of: {axes_text}
- One capsule per line
- No character names
- No second-person language (no "you")
- No plot or scene description
- Use simple, everyday words
- Each sentence under 18 words
- Do not add explanations or headers

Movie premise:
{premise}
"""

    response = client.responses.create(
        model="gpt-4o-mini",
        input=prompt
    )

    return response.output_text.strip()
