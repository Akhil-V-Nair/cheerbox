#!/usr/bin/env python3
"""
jobs/transform/build_silver_movies.py

Reads bronze movie files, dedupes by TMDb movie_id,
merges source categories, performs data quality checks,
and writes a clean silver file with only necessary fields.
"""

import os
import json
import unicodedata
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRONZE_DIR = ROOT / "data" / "bronze"
SILVER_DIR = ROOT / "data" / "silver"


# ---------------------------------------------------------
# Unicode + Text Cleaning
# ---------------------------------------------------------
def clean_text(value):
    if not value:
        return value

    # Normalize Unicode (fix accents, dots, quotes, WALL·E stays correct)
    value = unicodedata.normalize("NFKC", value)

    # Remove control chars / zero-width chars
    value = "".join(ch for ch in value if ch.isprintable())

    return value.strip()


def is_valid_imdb(imdb_id):
    """
    Valid IMDb format: tt + 7+ digits
    """
    if not imdb_id:
        return False
    return bool(re.match(r"tt\d{7,}", imdb_id))


# ---------------------------------------------------------
# Load bronze JSON files
# ---------------------------------------------------------
def load_bronze_files():
    files = [f for f in BRONZE_DIR.glob("*_raw.json") if f.is_file()]
    all_movies = []

    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            all_movies.extend(data)

    print(f"[+] Loaded {len(files)} bronze files")
    print(f"[+] Total rows loaded: {len(all_movies)}")
    return all_movies


# ---------------------------------------------------------
# Merge + Dedupe with Quality Checks
# ---------------------------------------------------------
def merge_movies(movies):
    """
    Dedupes by movie_id.
    Ensures data quality:
      - Clean unicode
      - Validate IMDb ID
      - Dedupe genres
      - Merge & sort source categories
    Keeps ONLY fields required downstream.
    """

    merged = {}

    for m in movies:
        mid = m["movie_id"]

        # -------------------------------
        # Data Quality checks
        # -------------------------------
        imdb_id = m.get("imdb_id")
        title = clean_text(m.get("title", ""))
        overview = clean_text(m.get("overview", ""))

        # Invalid → skip movie entirely
        if not title or not imdb_id or not is_valid_imdb(imdb_id):
            continue

        # Dedupe genres by ID
        raw_genres = m.get("genres", [])
        deduped_genres = list({g["id"]: g for g in raw_genres}.values())

        # Clean record fields
        clean_fields = {
            "movie_id": mid,
            "imdb_id": imdb_id,
            "title": title,
            "overview": overview,
            "poster_path": m.get("poster_path"),

            "vote_count": m.get("vote_count", 0),
            "vote_average": m.get("vote_average", 0.0),
            "popularity": m.get("popularity", 0.0),

            "genres": deduped_genres,
        }

        # -------------------------------
        # First occurrence → insert
        # -------------------------------
        if mid not in merged:
            clean_fields["source_categories"] = [m["source_category"]]
            merged[mid] = clean_fields
            continue

        # -------------------------------
        # Duplicate movie → merge
        # -------------------------------
        existing = merged[mid]

        # Merge categories
        existing["source_categories"].append(m["source_category"])
        existing["source_categories"] = sorted(list(set(existing["source_categories"])))

        # Keep best numeric metadata
        existing["vote_count"] = max(existing["vote_count"], clean_fields["vote_count"])
        existing["vote_average"] = max(existing["vote_average"], clean_fields["vote_average"])
        existing["popularity"] = max(existing["popularity"], clean_fields["popularity"])

        # Best overview: longest non-empty
        if len(clean_fields["overview"]) > len(existing["overview"]):
            existing["overview"] = clean_fields["overview"]

        # Better poster
        if not existing.get("poster_path") and clean_fields["poster_path"]:
            existing["poster_path"] = clean_fields["poster_path"]

        # Genres (deduped)
        existing["genres"] = clean_fields["genres"]

    return list(merged.values())


# ---------------------------------------------------------
# Save Silver Output
# ---------------------------------------------------------
def save_silver(movies):
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    outpath = SILVER_DIR / "movies_silver.json"

    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(movies, f, indent=2)

    print(f"[+] Saved {len(movies)} unique, clean movies → {outpath}")


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
def main():
    movies = load_bronze_files()
    merged = merge_movies(movies)
    save_silver(merged)


if __name__ == "__main__":
    main()
