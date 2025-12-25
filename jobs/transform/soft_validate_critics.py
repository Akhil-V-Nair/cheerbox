#!/usr/bin/env python3
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from pipeline.transform.critic_soft_validator import soft_validate_critic

CRITIC_FILE = ROOT / "data" / "gold" / "movie_critic_summaries.json"
MOVIES_FILE = ROOT / "data" / "gold" / "movies_gold.json"
OUT = ROOT / "data" / "gold" / "movie_critic_summaries_refined.json"


def main():
    critics = json.loads(CRITIC_FILE.read_text(encoding="utf-8"))
    movies = {
        m["movie_id"]: m
        for m in json.loads(MOVIES_FILE.read_text(encoding="utf-8"))
    }

    fixed = 0
    still_flagged = 0

    for c in critics:
        if c["validation"]["status"] != "flagged":
            continue

        movie = movies.get(c["movie_id"])
        if not movie:
            continue

        summary = c["critic_summary"]
        premise = movie.get("premise", "")

        ok, reason = soft_validate_critic(summary, premise)

        if ok:
            c["validation"] = {
                "status": "pass_soft",
                "reason": reason
            }
            fixed += 1
        else:
            c["validation"]["reason"] = reason
            still_flagged += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(critics, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[✓] Soft-validated: {fixed}")
    print(f"[!] Still flagged: {still_flagged}")
    print(f"[✓] Output → {OUT}")


if __name__ == "__main__":
    main()
