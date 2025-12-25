# cheerbox/pipeline/transform/critic_generator.py

def generate_critic_summary(client, title: str, premise: str, axes: list[str]) -> str:
    """
    Generates a human-sounding critic summary that explains
    WHY the movie emotionally works on audiences.
    """

    axes_text = ", ".join(axes)

    prompt = f"""
You are writing like a human film critic explaining audience reaction.

Write ONE paragraph (70–100 words).

Rules (VERY IMPORTANT):
- DO NOT describe plot events or scenes
- DO NOT praise filmmaking or use critic jargon
- DO NOT say: masterfully, intricately, explores, examines, delves
- DO NOT list themes
- DO explain how the movie makes viewers feel and why it stays with them
- Write like someone recommending the movie from experience

Movie title: {title}

Movie identity:
{premise}

Emotional tensions the movie operates on:
{axes_text}

Write naturally and plainly.
"""

    response = client.responses.create(
        model="gpt-4o-mini",
        input=prompt
    )

    return response.output_text.strip()
