#!/usr/bin/env python3

"""
TEST: Ontology-driven critic + emotional capsules
Model: gpt-4o-mini
Scope: First 5 movies ONLY
No writes. Console output only.
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

# -------------------------------------------------
# Environment
# -------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY missing")

from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

MODEL = "gpt-4o-mini"
SILVER = ROOT / "data" / "silver" / "movies_silver_validated.json"

TEST_MOVIE_COUNT = 5

# -------------------------------------------------
# Human-defined ontology
# -------------------------------------------------

EMOTIONAL_AXES = [
    "Belonging ↔ Isolation",
    "Agency ↔ Powerlessness",
    "Order ↔ Chaos",
    "Identity ↔ Mask",
    "Hope ↔ Despair",
    "Innocence ↔ Corruption",
    "Loyalty ↔ Betrayal",
    "Control ↔ Surrender",
    "Love ↔ Loss",
    "Truth ↔ Illusion",
    "Safety ↔ Threat",
    "Purpose ↔ Emptiness"
]

EMOTIONAL_TEXTURE = [
    "tender", "volatile", "wistful", "exhilarating", "oppressive",
    "defiant", "absurd", "melancholic", "triumphant", "uneasy"
]

# -------------------------------------------------
# Prompts
# -------------------------------------------------

def critic_prompt(title, overview, reviews):
    return f"""
You are a professional film critic.

Your task:
- Select EXACTLY **2 primary emotional axes**
- Select **1 secondary axis**
- Write ONE paragraph (80–110 words) analyzing the film

STRICT RULES:
- You MUST choose axes ONLY from the list provided
- DO NOT invent new themes
- DO NOT describe scenes or plot events
- Ground analysis in emotional tension and ideas
- No spoilers

ALLOWED EMOTIONAL AXES:
{chr(10).join(EMOTIONAL_AXES)}

Film Title:
{title}

Plot Overview:
{overview}

Audience Review Signals:
{reviews}

FORMAT:
Primary Axes:
- Axis 1
- Axis 2

Secondary Axis:
- Axis

Critic Paragraph:
"""

def capsule_prompt(title, axes, overview, reviews):
    return f"""
Generate exactly 5 emotional capsules for the film "{title}".

CONSTRAINTS:
- Each capsule MUST be anchored to ONE of these axes:
{axes}
- Use emotional texture words ONLY from this list:
{", ".join(EMOTIONAL_TEXTURE)}
- 2–3 sentences per capsule
- No plot details
- No clichés

Plot Overview:
{overview}

Audience Review Signals:
{reviews}

FORMAT FOR EACH CAPSULE:
Axis:
Texture:
Text:
"""

# -------------------------------------------------
# LLM Call
# -------------------------------------------------

def generate(prompt):
    resp = client.responses.create(
        model=MODEL,
        input=prompt
    )
    return resp.output_text.strip()

# -------------------------------------------------
# Test Runner
# -------------------------------------------------

def run_test():
    with open(SILVER, "r", encoding="utf-8") as f:
        movies = json.load(f)

    print(f"\n[TEST] Ontology-driven generation for {TEST_MOVIE_COUNT} movies\n")

    for m in movies[:TEST_MOVIE_COUNT]:
        print("=" * 100)
        print(f"MOVIE: {m['title']} (ID: {m['movie_id']})")
        print("=" * 100)

        overview = m.get("overview", "")
        reviews = "\n".join(
            r["content"] for r in m.get("validated_reviews", []) if r.get("keep")
        )[:1500]

        # Critic summary
        critic_out = generate(
            critic_prompt(m["title"], overview, reviews)
        )
        print("\n--- CRITIC ANALYSIS ---\n")
        print(critic_out)

        # Extract axes from critic output (simple heuristic)
        used_axes = [
            line.strip("- ").strip()
            for line in critic_out.splitlines()
            if "↔" in line
        ]

        axes_text = "\n".join(used_axes) if used_axes else "\n".join(EMOTIONAL_AXES[:3])

        # Capsules
        capsules_out = generate(
            capsule_prompt(m["title"], axes_text, overview, reviews)
        )
        print("\n--- EMOTIONAL CAPSULES ---\n")
        print(capsules_out)
        print("\n")

if __name__ == "__main__":
    run_test()
