#!/usr/bin/env python3
"""
Idempotent DuckDB Sanity Tests
Validates:
- movie counts
- genre counts
- category counts
- referential integrity
- missing or orphaned entries
"""

import duckdb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "cheerbox.db"


def run():
    print(f"[*] Connecting to DuckDB at: {DB_PATH}\n")
    con = duckdb.connect(DB_PATH)

    # ----------------------------
    # Basic counts
    # ----------------------------
    print("=== BASIC COUNTS ===")
    counts = con.execute("""
        SELECT
            (SELECT COUNT(*) FROM movies) AS movies_count,
            (SELECT COUNT(*) FROM genres) AS genres_count,
            (SELECT COUNT(*) FROM movie_genres) AS movie_genres_count,
            (SELECT COUNT(*) FROM movie_source_categories) AS movie_source_count;
    """).fetchdf()

    print(counts, "\n")

    # ----------------------------
    # Check duplicates
    # ----------------------------
    print("=== DUPLICATE CHECK ===")
    dup_movies = con.execute("""
        SELECT movie_id, COUNT(*) AS c
        FROM movies GROUP BY movie_id HAVING COUNT(*) > 1;
    """).fetchdf()

    print("Duplicate movies:\n", dup_movies if not dup_movies.empty else "✓ No duplicates", "\n")

    # ----------------------------
    # Check orphan movie_genres
    # ----------------------------
    print("=== ORPHAN GENRE MAPPINGS ===")
    orphan_genres = con.execute("""
        SELECT mg.*
        FROM movie_genres mg
        LEFT JOIN movies m ON m.movie_id = mg.movie_id
        WHERE m.movie_id IS NULL;
    """).fetchdf()

    print(orphan_genres if not orphan_genres.empty else "✓ No orphan movie_genres", "\n")

    # ----------------------------
    # Check orphan movie_source_categories
    # ----------------------------
    print("=== ORPHAN SOURCE CATEGORIES ===")
    orphan_source = con.execute("""
        SELECT sc.*
        FROM movie_source_categories sc
        LEFT JOIN movies m ON m.movie_id = sc.movie_id
        WHERE m.movie_id IS NULL;
    """).fetchdf()

    print(orphan_source if not orphan_source.empty else "✓ No orphan categories", "\n")

    # ----------------------------
    # Validate missing genre_movies
    # ----------------------------
    print("=== MOVIES WITHOUT GENRES ===")
    missing_genres = con.execute("""
        SELECT m.movie_id, m.title
        FROM movies m
        LEFT JOIN movie_genres mg ON mg.movie_id = m.movie_id
        WHERE mg.movie_id IS NULL;
    """).fetchdf()

    print(missing_genres if not missing_genres.empty else "✓ All movies have genre mappings", "\n")

    # ----------------------------
    # Validate missing source categories
    # ----------------------------
    print("=== MOVIES WITHOUT SOURCE CATEGORIES ===")
    missing_categories = con.execute("""
        SELECT m.movie_id, m.title
        FROM movies m
        LEFT JOIN movie_source_categories sc ON sc.movie_id = m.movie_id
        WHERE sc.movie_id IS NULL;
    """).fetchdf()

    print(missing_categories if not missing_categories.empty else "✓ All movies have source categories", "\n")

    # ----------------------------
    # Sample rows preview
    # ----------------------------
    print("=== SAMPLE MOVIES ===")
    sample = con.execute("""
        SELECT movie_id, title, vote_average, popularity
        FROM movies
        ORDER BY popularity DESC
        LIMIT 5;
    """).fetchdf()

    print(sample, "\n")

    con.close()
    print("✓ Tests complete.")


if __name__ == "__main__":
    run()
