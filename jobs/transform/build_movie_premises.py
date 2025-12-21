#!/usr/bin/env python3

import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# --------------------------------------------------
# Fix import path
# --------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# --------------------------------------------------
# Imports
# --------------------------------------------------
from pipeline.transform.premise_generator import generate_premise
from pipeline.transform.premise_validator import validate_premise

# --------------------------------------------------
# Paths
# --------------------------------------------------
SILVER = ROOT / "data" / "silver" / "movies_silver_validated.json"
OUT = ROOT / "data" / "gold" / "movie_premises.json"

# --------------------------------------------------
# Setup
# --------------------------------------------------
load_dotenv(ROOT / ".env")
client = OpenAI()

# --------------------------------------------------
def main():
    movies = json.loads(SILVER.read_text(encoding="utf-8"))
    results = []

    for m in movies:
        title = m["title"]
        overview = m.get("overview", "")
        genres = m.get("genres", [])

        premise = generate_premise(client, title, overview)
        valid, reason = validate_premise(premise, genres)

        # One retry only
        if not valid:
            premise = generate_premise(client, title, overview)
            valid, reason = validate_premise(premise, genres)

        results.append({
            "movie_id": m["movie_id"],
            "title": title,
            "premise": premise,
            "validation": {
            "status": "soft_pass",
            "reason": "missing_genre_keyword"
            }
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    flagged = sum(1 for r in results if r["validation"]["status"] != "pass")
    print(f"[✓] Premises generated: {len(results)}")
    print(f"[!] Flagged premises: {flagged}")

# --------------------------------------------------
if __name__ == "__main__":
    main()
