from openai import OpenAI

MODEL = "gpt-4o-mini"

def generate_critic_summary(client: OpenAI, *, title: str, premise: str, axes: list[str]) -> str:
    """
    Generates a single-paragraph critic summary grounded in premise + axes.
    """

    axis_text = ", ".join(axes)

    prompt = f"""
You are a professional film critic.

Write ONE paragraph (80–110 words).

Rules:
- Do NOT describe scenes, plot events, or characters.
- Do NOT quote dialogue.
- Do NOT use abstract academic language.
- Ground the analysis in the movie's core premise.
- Use the emotional tension implied by these axes:
  {axis_text}

The paragraph must feel specific to THIS movie.

Movie title: {title}
Core premise: {premise}
"""

    resp = client.responses.create(
        model=MODEL,
        input=prompt
    )

    return resp.output_text.strip()
