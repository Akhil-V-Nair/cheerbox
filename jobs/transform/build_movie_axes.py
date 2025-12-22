#!/usr/bin/env python3

import sys
from pathlib import Path

# --------------------------------------------------
# Ensure project root is on PYTHONPATH
# --------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import json
from pipeline.transform.axis_selector import select_axes

SILVER = ROOT / "data" / "silver" / "movies_silver_validated.json"
CHARACTERS = ROOT / "data" / "gold" / "movie_character_anchors.json"
OUT = ROOT / "data" / "gold" / "movie_axes.json"

def main():
    movies = json.loads(SILVER.read_text(encoding="utf-8"))
    char_map = {
        m["movie_id"]: m.get("character_anchors", [])
        for m in json.loads(CHARACTERS.read_text(encoding="utf-8"))
    }

    results = []

    for m in movies:
        axes = select_axes(
            genres=m.get("genres", []),
            premise=m.get("premise", ""),
            character_anchors=char_map.get(m["movie_id"], [])
        )

        results.append({
            "movie_id": m["movie_id"],
            "title": m["title"],
            "axes": axes
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print(f"[✓] Axes generated for {len(results)} movies")

if __name__ == "__main__":
    main()
