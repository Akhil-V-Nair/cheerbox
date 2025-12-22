#!/usr/bin/env python3

import json
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from pipeline.transform.character_anchor_extractor import extract_character_anchors
from pipeline.transform.character_anchor_validator import validate_character_anchors

INPUT = ROOT / "data" / "gold" / "movie_premises.json"
OUTPUT = ROOT / "data" / "gold" / "movie_character_anchors.json"

load_dotenv(ROOT / ".env")
client = OpenAI()

def main():
    movies = json.loads(INPUT.read_text(encoding="utf-8"))
    results = []
    empty = 0

    for m in movies:
        anchors = extract_character_anchors(
            client,
            m["title"],
            m["premise"]
        )

        valid = validate_character_anchors(anchors)

        if not valid:
            empty += 1

        results.append({
            "movie_id": m["movie_id"],
            "title": m["title"],
            "premise": m["premise"],
            "character_anchors": valid
        })

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print(f"[✓] Processed {len(results)} movies")
    print(f"[!] Empty anchors: {empty}")

if __name__ == "__main__":
    main()
