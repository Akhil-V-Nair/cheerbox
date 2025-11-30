#!/usr/bin/env python3
"""
jobs/transform/build_gold_movies.py

Reads Silver movie dataset (JSON), normalizes into 4 Parquet tables:
- movies.parquet
- genres.parquet
- movie_genres.parquet
- movie_source_categories.parquet

This is the final Gold layer, optimized for DuckDB.
"""

import json
from pathlib import Path
import polars as pl

# Paths
ROOT = Path(__file__).resolve().parents[2]
SILVER_FILE = ROOT / "data" / "silver" / "movies_silver.json"
GOLD_DIR = ROOT / "data" / "gold"


# ---------------------------------------------------------
# Load Silver JSON
# ---------------------------------------------------------
def load_silver():
    if not SILVER_FILE.exists():
        raise FileNotFoundError(f"Silver file not found: {SILVER_FILE}")

    with open(SILVER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------
# Build normalized Gold tables
# ---------------------------------------------------------
def build_gold_tables(silver_movies):
    movies_rows = []
    genres_map = {}               # genre_id → genre_name
    movie_genres_rows = []
    source_categories_rows = []

    for m in silver_movies:
        mid = m["movie_id"]

        # ------------ 1. movies table ------------
        movies_rows.append({
            "movie_id": mid,
            "imdb_id": m["imdb_id"],
            "title": m["title"],
            "overview": m["overview"],
            "poster_path": m.get("poster_path"),
            "vote_count": m.get("vote_count", 0),
            "vote_average": m.get("vote_average", 0.0),
            "popularity": m.get("popularity", 0.0),
        })

        # ------------ 2. genres + movie_genres ------------
        for g in m.get("genres", []):
            gid, gname = g["id"], g["name"]
            genres_map[gid] = gname  # dedupe master list

            movie_genres_rows.append({
                "movie_id": mid,
                "genre_id": gid,
            })

        # ------------ 3. source categories ------------
        for cat in m.get("source_categories", []):
            source_categories_rows.append({
                "movie_id": mid,
                "source_category": cat
            })

    return movies_rows, genres_map, movie_genres_rows, source_categories_rows


# ---------------------------------------------------------
# Save to Parquet (DuckDB-ready)
# ---------------------------------------------------------
def save_parquet(movies, genres_map, movie_genres, source_categories):
    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    # 1. movies.parquet
    pl.DataFrame(movies).write_parquet(GOLD_DIR / "movies.parquet")

    # 2. genres.parquet
    genres_rows = [{"genre_id": gid, "genre_name": name} for gid, name in genres_map.items()]
    pl.DataFrame(genres_rows).write_parquet(GOLD_DIR / "genres.parquet")

    # 3. movie_genres.parquet
    pl.DataFrame(movie_genres).write_parquet(GOLD_DIR / "movie_genres.parquet")

    # 4. movie_source_categories.parquet
    pl.DataFrame(source_categories).write_parquet(GOLD_DIR / "movie_source_categories.parquet")

    print(f"[+] Gold Parquet tables created in {GOLD_DIR}")


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
def main():
    silver_movies = load_silver()
    movies, genres_map, movie_genres, source_categories = build_gold_tables(silver_movies)
    save_parquet(movies, genres_map, movie_genres, source_categories)


if __name__ == "__main__":
    main()
