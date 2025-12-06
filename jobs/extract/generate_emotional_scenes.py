#!/usr/bin/env python3
"""
jobs/transform/generate_emotional_scenes.py

Generates 5 emotional paragraphs per movie using:
- TMDB overview
- Top user reviews
- Critic-style summaries (derived from reviews)
- The movie’s source categories + TMDB genres

Writes output to data/gold/emotional_scenes.parquet
"""

import os
import json
import time
from pathlib import Path
from typing import List, Dict
import polars as pl
from dotenv import load_dotenv
from openai import OpenAI

# -----------------------------
# Setup
# -----------------------------

ROOT = Path(__file__).resolve().parents[2]
SILVER_DIR = ROOT / "data" / "silver"
GOLD_DIR = ROOT / "data" / "gold"

load_dotenv(ROOT / ".env")

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_KEY:
    raise ValueError("OPENAI_API_KEY missing in .env")

client = OpenAI(api_key=OPENAI_KEY)


# -----------------------------
# TMDB review fetcher (stub; easy to expand)
# -----------------------------
import requests

TMDB_TOKEN = os.getenv("TMDB_BEARER_TOKEN")
if not TMDB_TOKEN:
    raise ValueError("TMDB_BEARER_TOKEN missing.")

TMDB_HEADERS = {
    "Authorization": f"Bearer {TMDB_TOKEN}",
    "Content-Type": "application/json;charset=utf-8"
}

def fetch_reviews(movie_id: int, limit: int = 10) -> List[str]:
    """
    Fetch top user reviews from TMDB.
    """
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/reviews"
    resp = requests.get(url, headers=TMDB_HEADERS)
    resp.raise_for_status()

    data = resp.json().get("results", [])
    snippets = []

    for r in data[:limit]:
        content = r.get("content", "")
        if content:
            snippets.append(content.strip())

    return snippets


# -----------------------------
# LLM PROMPT
# -----------------------------

def build_prompt(movie: Dict, overview: str, user_reviews: List[str]) -> str:
    return f"""
You are generating strictly 5 emotional scene paragraphs for a movie.

These are NOT real scenes. They MUST NOT contain copyrighted dialogue or plot specifics.
They are emotional vignettes inspired ONLY by:
- The movie overview
- User review feelings
- Critic-like sentiments extracted from reviews
- Source categories: {movie['source_categories']}
- TMDB genres: {movie['genres']}

Each paragraph MUST:
- Be 3–5 sentences
- Reflect the blended emotional tones of ALL source categories
- Match the cinematic tone suggested by TMDB genres
- Show strong emotional intensity (not mild)
- NOT invent events, names, or details not implied by the inputs
- Be distinct from the others

Movie Title: {movie['title']}

Overview:
{overview}

User Sentiment Snippets:
{json.dumps(user_reviews, indent=2)}

Now produce JSON with exactly this structure:

{{
  "paragraphs": [
    "paragraph_1",
    "paragraph_2",
    "paragraph_3",
    "paragraph_4",
    "paragraph_5"
  ]
}}
"""


# -----------------------------
# LLM CALL
# -----------------------------
def generate_paragraphs(movie, overview, reviews):
    prompt = build_prompt(movie, overview, reviews)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600
    )
    
    text = response.choices[0].message.content

    # Parse JSON
    try:
        data = json.loads(text)
        paragraphs = data.get("paragraphs", [])
        return paragraphs
    except Exception:
        print("LLM JSON parsing failed, retrying with safe extraction...")
        raise


# -----------------------------
# MAIN
# -----------------------------
def main():
    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    # Load movies
    silver_path = SILVER_DIR / "movies_silver.json"
    movies = json.load(open(silver_path, "r", encoding="utf-8"))

    out_rows = []

    print(f"Loaded {len(movies)} movies. Generating emotional scenes...")

    for m in movies:
        movie_id = m["movie_id"]
        print(f"\n→ Processing {m['title']} (id {movie_id})")

        # 1. Overview already in silver
        overview = m.get("overview", "")

        # 2. Fetch user reviews
        users = fetch_reviews(movie_id)
        if not users:
            users = ["No strong user review sentiments available."]

        # 3. Call LLM
        try:
            paragraphs = generate_paragraphs(m, overview, users)
        except:
            print("Retrying generation...")
            time.sleep(1)
            paragraphs = generate_paragraphs(m, overview, users)

        # Validate length × count
        if len(paragraphs) != 5:
            print("Invalid count, regenerating once...")
            paragraphs = generate_paragraphs(m, overview, users)

        out_rows.append({
            "movie_id": movie_id,
            "imdb_id": m.get("imdb_id"),
            "title": m["title"],
            "source_categories": m["source_categories"],
            "genres": m["genres"],
            "paragraphs": paragraphs
        })

        time.sleep(0.2)

    # Save as parquet
    df = pl.DataFrame(out_rows)
    outpath = GOLD_DIR / "emotional_scenes.parquet"
    df.write_parquet(outpath)

    print(f"\n[✓] Saved emotional scene dataset → {outpath}")


if __name__ == "__main__":
    main()
