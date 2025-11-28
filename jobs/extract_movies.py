#!/usr/bin/env python3
"""
jobs/extract_movies.py

Orchestrator script that uses pipeline/extract/tmdb_extractor.py
to fetch movie metadata for the target genres and write raw JSON
into the bronze layer.

Run from project root:
    python jobs/extract_movies.py
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Ensure project root is on sys.path so we can import pipeline modules
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

# now import the TMDB client & extractor
from pipeline.extract.tmdb_extractor import TMDBClient, MovieExtractor

# load env
load_dotenv(ROOT / ".env")

# --- CONFIG ----
# Target categories mapped to TMDb genre NAMES (not IDs).
TARGET_GENRES = {
    "comedy": ["Comedy"],
    "drama": ["Drama"],
    "romance": ["Romance"],
    "action_adventure": ["Action", "Adventure"],
    "sci_fi_fantasy": ["Science Fiction", "Fantasy"],
    "murder_mystery": ["Mystery"]
}

# Per-genre final limit after dedupe
PER_GENRE_LIMIT = 1000

# ----------------

def dedupe_and_sort(movies):
    """Dedupe by movie_id and sort by vote_average desc, vote_count desc, popularity desc."""
    seen = {}
    for m in movies:
        mid = m.get("movie_id")
        if mid is None:
            continue
        # keep the entry with highest vote_count if duplicates exist
        if mid not in seen or (m.get("vote_count", 0) > seen[mid].get("vote_count", 0)):
            seen[mid] = m
    deduped = list(seen.values())
    deduped.sort(key=lambda x: (
        x.get("vote_average") if x.get("vote_average") is not None else 0,
        x.get("vote_count", 0),
        x.get("popularity", 0)
    ), reverse=True)
    return deduped

def main():
    bearer = os.getenv("TMDB_BEARER_TOKEN")
    if not bearer:
        print("TMDB_BEARER_TOKEN missing. Add it to .env in project root.")
        return

    client = TMDBClient(bearer)
    extractor = MovieExtractor(client, verbose=True)

    # Resolve genre name -> [ids]
    resolved = extractor.resolve_genre_ids(TARGET_GENRES)
    print("Resolved genre IDs:", resolved)

    all_master = []

    for genre_label, id_list in resolved.items():
        print(f"\n=== Processing genre: {genre_label} (ids: {id_list}) ===")
        combined = []

        for gid in id_list:
            # Fetch up to PER_GENRE_LIMIT per ID, but we'll dedupe+limit after merging
            print(f" -> Fetching movies for TMDb genre id {gid} ...")
            movies = extractor.fetch_top_movies_for_genre(gid, limit=PER_GENRE_LIMIT)
            print(f"    fetched {len(movies)} entries for id {gid}")
            combined.extend(movies)

        print(f"  Merged {len(combined)} raw entries for genre label '{genre_label}'. Deduping & sorting...")
        final_list = dedupe_and_sort(combined)

        # Trim to PER_GENRE_LIMIT final
        if len(final_list) > PER_GENRE_LIMIT:
            final_list = final_list[:PER_GENRE_LIMIT]

        print(f"  Final {len(final_list)} movies for genre '{genre_label}' (after dedupe & trim).")

        # save per-genre raw file
        extractor.save_raw_movies(genre_label, final_list)

        # accumulate to master list (avoid duplicates across genres later)
        all_master.extend(final_list)

    # Create a master deduped file across all genres
    master_final = dedupe_and_sort(all_master)
    master_path = Path(extractor.bronze_path) / "all_movies_master.json"
    with open(master_path, "w", encoding="utf-8") as f:
        json.dump(master_final, f, indent=2)
    print(f"\n[+] Saved master movie list with {len(master_final)} unique movies → {master_path}")

if __name__ == "__main__":
    main()
