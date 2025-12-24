#!/usr/bin/env python3
"""
Merge all Gold-level movie artifacts into a single canonical file.

Inputs:
- data/gold/movie_premises.json
- data/gold/movie_axes.json
- data/gold/movie_character_anchors.json

Output:
- data/gold/movies_gold.json
"""

import json
from pathlib import Path

# -------------------------------------------------
# Paths (NO pipeline imports, NO sys.path hacks)
# -------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]

PREMISES_FILE = ROOT / "data" / "gold" / "movie_premises.json"
AXES_FILE = ROOT / "data" / "gold" / "movie_axes.json"
ANCHORS_FILE = ROOT / "data" / "gold" / "movie_character_anchors.json"

OUT_FILE = ROOT / "data" / "gold" / "movies_gold.json"


def load_indexed(path, key="movie_id"):
    """Load a list of dicts and index by movie_id."""
    if not path.exists():
        return {}

    items = json.loads(path.read_text(encoding="utf-8"))
    return {item[key]: item for item in items}


def main():
    print("[*] Loading gold artifacts...")

    premises = load_indexed(PREMISES_FILE)
    axes = load_indexed(AXES_FILE)
    anchors = load_indexed(ANCHORS_FILE)

    all_movie_ids = set(premises) | set(axes) | set(anchors)

    merged = []

    for movie_id in sorted(all_movie_ids):
        p = premises.get(movie_id, {})
        a = axes.get(movie_id, {})
        c = anchors.get(movie_id, {})

        merged.append({
            "movie_id": movie_id,
            "title": p.get("title") or a.get("title") or c.get("title"),

            "premise": p.get("premise", "").strip(),

            "axes": a.get("axes", []),

            "character_anchors": c.get("character_anchors", [])
        })

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(
        json.dumps(merged, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"[✓] Gold movies merged: {len(merged)}")
    print(f"[✓] Output written to: {OUT_FILE}")


if __name__ == "__main__":
    main()
