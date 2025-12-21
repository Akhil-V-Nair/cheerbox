# pipeline/transform/critic_extractor.py

import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv

from pathlib import Path

# Load environment
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

from openai import OpenAI
client = OpenAI()

# Faster + cheaper model
MODEL = "gpt-4o-mini"     # MUCH faster than 4.1-mini and reliable


# ---------------------------------------------------------
#  Select strongest review snippets
# ---------------------------------------------------------
def select_review_snippets(validated_reviews: List[Dict], max_snippets: int = 5) -> List[str]:
    ranked = [
        r for r in validated_reviews
        if r.get("keep") and r.get("content")
    ]

    ranked = sorted(
        ranked,
        key=lambda x: (
            x["relevance"]["score"],
            x["length"]
        ),
        reverse=True
    )

    return [r["content"] for r in ranked[:max_snippets]]


# ---------------------------------------------------------
#  Critic Summary Prompt — Updated & Strict
# ---------------------------------------------------------
def build_critic_prompt(title: str, overview: str, genres: List[str], review_snippets: List[str]):
    genre_str = ", ".join(genres)
    snippets = "\n".join(f"- {s}" for s in review_snippets)

    return f"""
You are a professional film critic with expert-level knowledge of cinema history, genre conventions, and thematic analysis.

Write ONE paragraph (80–120 words) that analyzes the film’s broader thematic ideas.

Allowed:
- using your general knowledge of the movie's reputation
- referencing tonal qualities, emotional atmosphere, thematic patterns
- high-level insights consistent with known critical discourse

Forbidden:
- describing scenes
- summarizing plot events
- referencing named characters
- quoting or paraphrasing dialogue
- revealing spoilers
- listing genre categories as themes

Focus only on:
- emotional tone
- philosophical/psychological concerns
- recurring motifs that appear in films of this kind
- patterns echoed in audience reviews

When drawing on prior knowledge, keep it thematic — NEVER descriptive.

Film Title: {title}
Genres: {genre_str}

Overview:
{overview}

Key Audience Review Signals:
{snippets}

Your Output:
One cohesive thematic paragraph, no more than 120 words.
"""


# ---------------------------------------------------------
#  Emotional Capsules Prompt — STRICT THEME RULES
# ---------------------------------------------------------
def build_emotional_capsules_prompt(title: str, overview: str, genres: List[str], review_snippets: List[str]):
    genre_str = ", ".join(genres)
    snippets = "\n".join(f"- {s}" for s in review_snippets)

    return f"""
You are an expert narrative analyst.

Generate **5 emotional capsules** for the film *{title}*.
Each capsule must be 3–5 sentences.

STRICT RULES:

THE "theme" FIELD:
✔ MUST be an abstract emotional or narrative motif.
✔ MUST sound like literary analysis:
   - "Burden of Expectation"
   - "Longing for Belonging"
   - "Cycles of Regret"
   - "Confronting Inner Chaos"
   - "Redemption Through Connection"
✘ MUST NOT be a genre label such as:
   "Action", "Comedy", "Sci-Fi", "Adventure", "Romance", "Drama"

THE "emotion" FIELD:
✔ MUST be a single emotional descriptor:
   - "melancholic", "hopeful", "tense", "anxious", "wistful", etc.

CONTENT RULES:
✘ No scene descriptions
✘ No plot summaries
✘ No recognizable events
✘ No named characters
✘ No dialogue of any kind

ALLOWED:
✔ High-level emotional archetypes
✔ Connections inspired by reviews
✔ Tone/style consistent with genres: {genre_str}

FILM OVERVIEW:
{overview}

AUDIENCE REVIEW SIGNALS:
{snippets}

Output EXACTLY this JSON structure:

[
  {{
    "theme": "...",
    "emotion": "...",
    "text": "3–5 sentences..."
  }},
  ...
]
"""


# ---------------------------------------------------------
#  Main generation logic
# ---------------------------------------------------------
def generate_movie_themes_and_capsules(movie: Dict[str, Any]) -> Dict[str, Any]:

    title = movie["title"]
    overview = movie.get("overview", "")
    genres = [g["name"] for g in movie.get("genres", [])]

    validated_reviews = movie.get("validated_reviews", [])
    review_snippets = select_review_snippets(validated_reviews, max_snippets=5)

    critic_prompt = build_critic_prompt(title, overview, genres, review_snippets)
    capsule_prompt = build_emotional_capsules_prompt(title, overview, genres, review_snippets)

    # ---------- Critic Summary ----------
    critic_resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You produce high-quality thematic film analysis."},
            {"role": "user", "content": critic_prompt}
        ],
        temperature=0.4,
        max_tokens=250
    )
    critic_summary = critic_resp.choices[0].message.content.strip()

    # ---------- Emotional Capsules ----------
    capsule_resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You generate emotional narrative archetypes without scene details."},
            {"role": "user", "content": capsule_prompt}
        ],
        temperature=0.5,
        max_tokens=600
    )

    capsules_text = capsule_resp.choices[0].message.content.strip()

    try:
        capsules = json.loads(capsules_text)
    except Exception:
        capsules = [{"theme": "Unknown Motif", "emotion": "neutral", "text": capsules_text}]

    return {
        "movie_id": movie["movie_id"],
        "title": title,
        "critic_summary": critic_summary,
        "emotional_capsules": capsules
    }
