#!/usr/bin/env python3
"""
TEST SCRIPT — Literal Narrative Premise Extraction

Purpose:
- Extract a strict, factual "Literal Narrative Premise" for movies
- NO writing to pipeline
- Console output only
- Used to calibrate prompt + constraints

Rules enforced:
- 6–12 words
- No emotions
- No themes
- No metaphors
- No genre labels
"""

import os
import json
import re
from pathlib import Path
from dotenv import load_dotenv

# -------------------------------------------------
# Load environment
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
# Prompt
# -------------------------------------------------

def premise_prompt(title, overview):
    return f"""
You are extracting a literal narrative premise for a movie.

Write ONE short phrase that describes what the movie is literally about.

Rules (strict):
- 6 to 12 words
- No metaphors
- No emotions
- No themes
- No symbolism
- No genre labels
- No poetic language
- Describe only the story-world setup or situation

Bad examples:
- "a journey of self-discovery"
- "exploring love and loss"
- "chaos versus order"

Movie title:
{title}

Plot overview:
{overview}

Write ONLY the premise phrase.
"""

# -------------------------------------------------
# Validation
# -------------------------------------------------

GENERIC_WORDS = {
    "love", "loss", "identity", "purpose", "meaning", "journey",
    "struggle", "redemption", "belonging", "hope", "despair",
    "chaos", "order", "emotion", "fate"
}

def is_valid_premise(text):
    words = text.lower().split()

    if not (6 <= len(words) <= 12):
        return False, "word_count"

    if any(w in GENERIC_WORDS for w in words):
        return False, "generic_word"

    if "," in text:
        return False, "comma_used"

    if not re.match(r"^[a-zA-Z0-9\s\-\.,']+$", text):
        return False, "invalid_characters"

    return True, None

# -------------------------------------------------
# LLM Call
# -------------------------------------------------

def generate_premise(title, overview):
    resp = client.responses.create(
        model=MODEL,
        input=premise_prompt(title, overview)
    )
    return resp.output_text.strip()

# -------------------------------------------------
# Test Runner
# -------------------------------------------------

def run_test():
    with open(SILVER, "r", encoding="utf-8") as f:
        movies = json.load(f)

    print(f"\n[TEST] Literal Premise Extraction — {TEST_MOVIE_COUNT} movies\n")

    for m in movies[:TEST_MOVIE_COUNT]:
        title = m["title"]
        overview = m.get("overview", "")

        print("=" * 90)
        print(f"MOVIE: {title} (ID: {m['movie_id']})")
        print("=" * 90)

        premise = generate_premise(title, overview)
        valid, reason = is_valid_premise(premise)

        if not valid:
            print(f"[!] Invalid premise ({reason}) → regenerating once")
            premise = generate_premise(title, overview)
            valid, reason = is_valid_premise(premise)

        status = "✓ VALID" if valid else f"✗ INVALID ({reason})"
        print(f"Premise: {premise}")
        print(f"Status: {status}\n")

if __name__ == "__main__":
    run_test()
