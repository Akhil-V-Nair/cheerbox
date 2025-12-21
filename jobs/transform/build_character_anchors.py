#!/usr/bin/env python3

import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


from pipeline.transform.character_anchor_extractor import extract_character_anchors
from pipeline.transform.character_anchor_validator import validate_character_anchors


INPUT = ROOT / "data" / "gold" / "movie_premises.json"
OUTPUT = ROOT / "data" / "gold" / "movie_character_anchors.json"

# --------------------------------------------------
# Init
# --------------------------------------------------
load_dotenv(ROOT / ".env")
client = OpenAI()

# --------------------------------------------------
# Main
# --------------------------------------------------
def main():
    movies = json.loads(INPUT.read_text(encoding="utf-8"))
    results = []

    empty_count = 0

    for m in movies:
        anchors = extract_character_anchors(
            client=client,
            title=m["title"],
            premise=m["premise"]
        )

        valid_anchors = validate_character_anchors(anchors)

        if not valid_anchors:
            empty_count += 1

        results.append({
            "movie_id": m["movie_id"],
            "title": m["title"],
            "premise": m["premise"],
            "character_anchors": valid_anchors
        })

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print(f"[✓] Character anchors generated for {len(results)} movies")
    print(f"[!] Movies with no valid anchors: {empty_count}")

if __name__ == "__main__":
    main()
