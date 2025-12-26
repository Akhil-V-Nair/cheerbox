#!/usr/bin/env python3

import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# --------------------------------------------------
# Fix imports permanently
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


def parse_capsules(text, axes):
    capsules = []

    for line in text.splitlines():
        if "::" not in line:
            continue

        parts = [p.strip() for p in line.split("::", 2)]
        if len(parts) != 3:
            continue

        axis, emotion, sentence = parts

        if axis not in axes:
            continue

        capsules.append({
            "axis": axis,
            "emotion": emotion,
            "text": sentence
        })

    return capsules


def main():
    movies = json.loads(GOLD_IN.read_text(encoding="utf-8"))
    results = []

    generated = 0
    flagged = 0

    for m in movies:
        movie_id = m["movie_id"]
        title = m["title"]
        premise = m.get("premise", "").strip()
        axes = m.get("axes", [])

        if not premise or not axes:
            results.append({
                "movie_id": movie_id,
                "title": title,
                "emotional_capsules": [],
                "validation": {
                    "status": "skipped",
                    "reason": "missing_inputs"
                }
            })
            continue

        raw_text = ""
        capsules = []
        valid = False
        reason = "unknown"

        for _ in range(MAX_RETRIES):
            raw_text = generate_emotional_capsules(
                client,
                title=title,
                premise=premise,
                axes=axes
            )

            capsules = parse_capsules(raw_text, axes)
            valid, reason = validate_emotional_capsules(capsules, axes)

            if valid:
                break

        if valid:
            generated += 1
            status = "pass"
        else:
            flagged += 1
            status = "flagged"

        # IMPORTANT: Never drop capsules
        results.append({
            "movie_id": movie_id,
            "title": title,
            "emotional_capsules": capsules,
            "validation": {
                "status": status,
                "reason": reason
            }
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"[✓] Generated: {generated}")
    print(f"[!] Flagged: {flagged}")
    print(f"[✓] Output → {OUT}")


if __name__ == "__main__":
    main()
