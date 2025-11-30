#!/usr/bin/env python3
"""
jobs/extract_movies.py

Fetch movie metadata for 6 target genres and save
each genre independently into data/bronze/.
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from pipeline.extract.tmdb_extractor import TMDBClient, MovieExtractor

load_dotenv(ROOT / ".env")

TARGET_GENRES = {
    "comedy": ["Comedy"],
    "drama": ["Drama"],
    "romance": ["Romance"],
    "action_adventure": ["Action", "Adventure"],
    "sci_fi_fantasy": ["Science Fiction", "Fantasy"],
    "murder_mystery": ["Mystery"]
}

PER_GENRE_LIMIT = 1000


def dedupe_movies(movies):
    seen = {}
    for m in movies:
        mid = m["movie_id"]
        if mid not in seen:
            seen[mid] = m
    return list(seen.values())


def main():
    bearer = os.getenv("TMDB_BEARER_TOKEN")
    client = TMDBClient(bearer)
    extractor = MovieExtractor(client, verbose=True)

    resolved = extractor.resolve_genre_ids(TARGET_GENRES)
    print("\nResolved Genre Map:")
    print(resolved)

    for label, genre_list in resolved.items():
        print(f"\n=== Processing {label} ===")

        combined = []

        # Step 1: Fetch base movie metadata (FAST, no IMDb yet)
        for genre_info in genre_list:
            movies = extractor.fetch_movies_basic(
                genre_info, 
                limit=PER_GENRE_LIMIT, 
                source_category=label   # NEW
            )
            combined.extend(movies)

        # Step 2: Dedupe
        final_list = dedupe_movies(combined)

        print(f"  → {len(final_list)} movies after dedupe; narrowing to top 50...")

        # Step 2.1: Sort + keep top 50 only
        final_list = sorted(
            final_list,
            key=lambda m: (
                m.get("vote_count", 0),
                m.get("vote_average", 0),
                m.get("popularity", 0)
            ),
            reverse=True
        )[:50]

        print(f"  → {len(final_list)} movies kept after ranking (top 50). Now attaching REAL genres...")

        # 🔥 Step 3: Attach TRUE TMDb genres
        final_list = extractor.attach_real_genres(final_list)

        print("  → Real genres attached. Now attaching IMDb IDs...")

        # 🔥 Step 4: Attach IMDb IDs
        final_list = extractor.attach_imdb_ids(final_list)

        # Step 5: Save
        extractor.save_raw_movies(label, final_list)


if __name__ == "__main__":
    main()
