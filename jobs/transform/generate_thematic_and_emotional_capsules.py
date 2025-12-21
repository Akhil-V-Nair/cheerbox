#!/usr/bin/env python3

"""
Generates:
  data/silver/movies_thematic_and_emotional.json

Input:
  data/silver/movies_silver_validated.json

Output for each movie:
  - critic_summary
  - emotional_capsules (5 per movie)
"""

import json
import time
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from pipeline.transform.critic_extractor import generate_movie_themes_and_capsules

SILVER_IN = ROOT / "data" / "silver" / "movies_silver_validated.json"
OUT_FILE = ROOT / "data" / "silver" / "movies_thematic_and_emotional.json"


def main():
    with open(SILVER_IN, "r", encoding="utf-8") as f:
        movies = json.load(f)

    print(f"[+] Loaded {len(movies)} movies.")
    print("[*] Generating critic summaries and emotional capsules…")

    results = []

    for idx, movie in enumerate(movies, start=1):
        print(f" → ({idx}/{len(movies)}) {movie['title']}")

        try:
            entry = generate_movie_themes_and_capsules(movie)
            results.append(entry)
        except Exception as e:
            print(f"   !! Error for {movie['title']}: {e}")
            continue

        time.sleep(0.25)  # polite throttle

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n[✓] Saved → {OUT_FILE}")


if __name__ == "__main__":
    main()
