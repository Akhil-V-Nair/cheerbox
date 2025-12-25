#!/usr/bin/env python3

"""
Cleans flagged critic summaries WITHOUT regeneration.

Actions:
- Strip markdown / quotes
- Remove known generic critic phrases
- Normalize spacing
- Re-run validator
"""
import sys
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pipeline.transform.critic_validator import validate_critic_summary

# --------------------------------------------------
# Paths
# --------------------------------------------------

IN_PATH = ROOT / "data" / "gold" / "movie_critic_summaries.json"
OUT_PATH = ROOT / "data" / "gold" / "movie_critic_summaries_cleaned.json"

# --------------------------------------------------
# Generic phrases to remove (surgical)
# --------------------------------------------------
GENERIC_PHRASES = [
    "emotional journey",
    "deeply emotional",
    "thought-provoking experience",
    "explores themes of",
    "at its core",
    "ultimately",
    "serves as a reminder",
]

# --------------------------------------------------
# Cleanup helpers
# --------------------------------------------------
def clean_text(text: str) -> str:
    if not text:
        return ""

    # Remove markdown italics/bold
    text = re.sub(r"[*_]{1,2}([^*_]+)[*_]{1,2}", r"\1", text)

    # Strip leading/trailing quotes
    text = text.strip().strip('"').strip("'")

    # Remove excessive parentheses
    text = re.sub(r"\([^)]*\)", "", text)

    # Remove generic phrases
    for phrase in GENERIC_PHRASES:
        text = re.sub(
            r"\b" + re.escape(phrase) + r"\b",
            "",
            text,
            flags=re.IGNORECASE,
        )

    # Normalize whitespace
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\s+([.,])", r"\1", text)

    return text.strip()

# --------------------------------------------------
# Main
# --------------------------------------------------
def main():
    movies = json.loads(IN_PATH.read_text(encoding="utf-8"))

    cleaned = []
    fixed = 0
    still_flagged = 0

    for m in movies:
        status = m.get("validation", {}).get("status")

        if status != "flagged":
            cleaned.append(m)
            continue

        original = m.get("critic_summary", "")
        cleaned_text = clean_text(original)

        valid, reason = validate_critic_summary(cleaned_text)

        if valid:
            fixed += 1
            cleaned.append({
                **m,
                "critic_summary": cleaned_text,
                "validation": {
                    "status": "pass",
                    "reason": "cleaned"
                }
            })
        else:
            still_flagged += 1
            cleaned.append({
                **m,
                "critic_summary": cleaned_text,
                "validation": {
                    "status": "flagged",
                    "reason": reason
                }
            })

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps(cleaned, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"[✓] Fixed via cleanup: {fixed}")
    print(f"[!] Still flagged: {still_flagged}")
    print(f"[✓] Output → {OUT_PATH}")

if __name__ == "__main__":
    main()
