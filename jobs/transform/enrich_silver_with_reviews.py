#!/usr/bin/env python3

"""
jobs/transform/enrich_silver_with_reviews.py

Adds:
  - reviews (list[str])
  - reviews_missing (bool)

Reads from:
  - data/silver/movies_silver.json
  - data/bronze/reviews/<movie_id>.json

Outputs:
  - data/silver/movies_silver_enriched.json
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SILVER_IN = ROOT / "data" / "silver" / "movies_silver.json"
SILVER_OUT = ROOT / "data" / "silver" / "movies_silver_enriched.json"
REVIEWS_DIR = ROOT / "data" / "bronze" / "reviews"


# ---------------------------------------------------------
# Load reviews for 1 movie
# ---------------------------------------------------------
def load_reviews(movie_id: int):
    """
    Returns:
      list[str] reviews,
      bool missing_flag
    """

    path = REVIEWS_DIR / f"{movie_id}.json"

    # No file → missing
    if not path.exists():
        return [], True

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            # malformed file
            return [], True

        cleaned = []

        for r in data:
            content = r.get("content", "")
            if isinstance(content, str):
                text = content.strip()
                if text:         # skip empty reviews
                    cleaned.append(text)

        # If file exists but no valid reviews → still "not missing"
        return cleaned, False

    except Exception:
        # Any read/parse error → treat as missing
        return [], True


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
def main():
    # Load silver movies
    with open(SILVER_IN, "r", encoding="utf-8") as f:
        movies = json.load(f)

    print(f"[+] Loaded {len(movies)} movies from Silver")

    enriched = []
    missing_count = 0

    for m in movies:
        mid = m["movie_id"]
        reviews, missing = load_reviews(mid)

        m["reviews"] = reviews
        m["reviews_missing"] = missing

        if missing:
            missing_count += 1
            print(f"   ! Missing reviews for movie_id={mid} → '{m['title']}'")

        enriched.append(m)

    # Save enriched data
    SILVER_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(SILVER_OUT, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2)

    print("\n[✓] Enrichment complete")
    print(f"[✓] Output → {SILVER_OUT}")
    print(f"[✓] Movies with missing reviews: {missing_count}")
    print(f"[✓] Movies with reviews: {len(movies) - missing_count}")


if __name__ == "__main__":
    main()
