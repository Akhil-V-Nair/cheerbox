#!/usr/bin/env python3

import sys
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

PREMISES = ROOT / "data/gold/movie_premises.json"
AXES = ROOT / "data/gold/movie_axes.json"
OUT = ROOT / "data/gold/movie_identity.json"

def main():
    premises = {m["movie_id"]: m for m in json.loads(PREMISES.read_text())}
    axes = {m["movie_id"]: m for m in json.loads(AXES.read_text())}

    merged = []

    for movie_id, p in premises.items():
        a = axes.get(movie_id, {})

        merged.append({
            "movie_id": movie_id,
            "title": p["title"],
            "premise": p.get("premise", "").strip(),
            "axes": a.get("axes", [])
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(merged, indent=2), encoding="utf-8")

    print(f"[✓] Movie identity built: {len(merged)} movies")

if __name__ == "__main__":
    main()
