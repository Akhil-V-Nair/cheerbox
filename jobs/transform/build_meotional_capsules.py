#!/usr/bin/env python3

import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# --------------------------------------------------
# Fix import path permanently
# --------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from pipeline.transform.emotional_capsule_generator import generate_emotional_capsules
from pipeline.transform.emotional_capsule_validator import validate_emotional_capsules

# --------------------------------------------------
# Paths
# --------------------------------------------------
GOLD_IN = ROOT / "data" / "gold" / "movies_gold.json"
OUT = ROOT / "data" / "gold" / "movie_emotional_capsules.json"

# --------------------------------------------------
# Setup
# --------------------------------------------------
load_dotenv(ROOT / ".env")
client = OpenAI()

MAX_RETRIES = 2


def main():
    movies = json.loads(GOLD_IN.read_text(encoding="utf-8"))
    results = []

    generated = 0
    flagged = 0

    for m in movies:
        title = m["title"]
        premise = m.get("premise", "").strip()
        axes = m.get("axes", [])
        genre = m.get("genre", "")

        if not premise or not axes:
            results.append({
                "movie_id": m["movie_id"],
                "title": title,
                "emotional_capsules": [],
                "validation": {"status": "skipped", "reason": "missing_inputs"}
            })
            continue

        capsules_text = ""
        valid = False
        reason = "unknown"

        for _ in range(MAX_RETRIES):
            capsules_text = generate_emotional_capsules(
                client,
                title=title,
                premise=premise,
                axes=axes,
                genre=genre
            )

            valid, reason = validate_emotional_capsules(capsules_text, axes)
            if valid:
                break

        if valid:
            generated += 1
            capsules = json.loads(capsules_text)
            status = "pass"
        else:
            flagged += 1
            capsules = json.loads(capsules_text) if capsules_text else []
            status = "flagged"

        results.append({
            "movie_id": m["movie_id"],
            "title": title,
            "emotional_capsules": capsules,
            "validation": {"status": status, "reason": reason}
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[✓] Generated: {generated}")
    print(f"[!] Flagged: {flagged}")
    print(f"[✓] Output → {OUT}")


if __name__ == "__main__":
    main()
