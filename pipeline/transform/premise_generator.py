# pipeline/transform/premise_generator.py

def generate_premise(client, title: str, overview: str) -> str:
    """
    Generates a one-sentence concrete movie premise.
    The premise must describe WHAT the movie is about, literally.
    """

    prompt = f"""
You are generating a ONE-SENTENCE movie premise.

Rules:
- Describe the movie literally.
- No metaphors.
- No themes.
- No emotions.
- No abstract language.
- Must be understandable by someone who has never seen the movie.
- 10–15 words max.

Movie title: {title}

Overview:
{overview}

Write ONLY the premise sentence.
"""

    response = client.responses.create(
        model="gpt-4o-mini",
        input=prompt
    )

    return response.output_text.strip()
