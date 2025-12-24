#!/usr/bin/env python3

import json
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# ---------------------------------------------------
# PATH FIX — ensures NO module errors
# ---------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

load_dotenv(ROOT / ".env")

from pipeline.transform.axis_generator import generate_axes
from pipeline.transform.axis_validator import validate_axes

# ---------------------------------------------------
# FILES
# ---------------------------------------------------
SILVER = ROOT / "data" / "silver" / "movies_silver_validated.json"
OUT = ROOT / "data" / "gold" / "movie_axes.json"

client = OpenAI()

def main():
    movies = json.loads(SILVER.read_text(encoding="utf-8"))
    results = []

    for m in movies:
        title = m["title"]
        premise = m.get("premise", "")
        genres = [g["name"] for g in m.get("genres", [])]

        axes = generate_axes(client, title, premise, genres)
        validation = validate_axes(axes, genres)

        results.append({
            "movie_id": m["movie_id"],
            "title": title,
            "axes": axes,
            "validation": validation
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print(f"[✓] Axes generated for {len(results)} movies")

if __name__ == "__main__":
    main()
