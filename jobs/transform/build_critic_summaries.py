#!/usr/bin/env python3

import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# --------------------------------------------------
# Ensure project root is on PYTHONPATH (CRITICAL)
# --------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# --------------------------------------------------
# Now imports WILL work
# --------------------------------------------------
from pipeline.transform.critic_generator import generate_critic_summary
from pipeline.transform.critic_validator import validate_critic_summary

# --------------------------------------------------
# Paths
# --------------------------------------------------
GOLD_IN = ROOT / "data" / "gold" / "movies_gold.json"
OUT = ROOT / "data" / "gold" / "movie_critic_summaries.json"

# --------------------------------------------------
# Setup
# --------------------------------------------------
load_dotenv(ROOT / ".env")
client = OpenAI()

MAX_RETRIES = 2


def main():
    movies = json.loads(GOLD_IN.read_text(encoding="utf-8"))
    results = []

    skipped = 0
    generated = 0
    flagged = 0

    for m in movies:
        movie_id = m["movie_id"]
        title = m.get("title")
        premise = (m.get("premise") or "").strip()
        axes = m.get("axes") or []

        if not premise or not axes:
            skipped += 1
            results.append({
                "movie_id": movie_id,
                "title": title,
                "critic_summary": "",
                "validation": {
                    "status": "skipped",
                    "reason": "missing_inputs"
                }
            })
            continue

        summary = ""
        valid = False
        reason = "unknown"

        for _ in range(MAX_RETRIES):
            summary = generate_critic_summary(
                client,
                title=title,
                premise=premise,
                axes=axes
            )

            valid, reason = validate_critic_summary(summary)
            if valid:
                break

        if valid:
            generated += 1
            status = "pass"
        else:
            flagged += 1
            status = "flagged"

        results.append({
            "movie_id": movie_id,
            "title": title,
            "critic_summary": summary if valid else "",
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

    print(f"[✓] Critic summaries generated: {generated}")
    print(f"[!] Flagged: {flagged}")
    print(f"[–] Skipped: {skipped}")
    print(f"[✓] Output → {OUT}")


if __name__ == "__main__":
    main()
