#!/usr/bin/env python3

import json
from pathlib import Path
import time
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))


from pipeline.extract.reviews_extractor import ReviewExtractor

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

SILVER = ROOT / "data" / "silver" / "movies_silver.json"
OUT_DIR = ROOT / "data" / "bronze" / "reviews"

def main():
    extractor = ReviewExtractor(save_dir=OUT_DIR)

    with open(SILVER, "r", encoding="utf-8") as f:
        movies = json.load(f)

    print(f"Loaded {len(movies)} movies from Silver")

    for m in movies:
        movie_id = m["movie_id"]
        print(f"→ Fetching reviews for {movie_id} - {m['title']}")

        reviews = extractor.fetch_reviews(movie_id)
        if not reviews:
            print("   No reviews found.")
            continue

        path = extractor.save(movie_id, reviews)
        print(f"   Saved {len(reviews)} reviews → {path}")

        time.sleep(0.25)  # polite rate-limit

if __name__ == "__main__":
    main()
