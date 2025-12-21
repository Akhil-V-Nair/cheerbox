#!/usr/bin/env python3
"""
jobs/transform/validate_reviews.py

Optimized version:
 - Pre-calculates context embeddings ONCE per movie.
 - Uses fast relevance scoring without recomputing embeddings.
 - Dedup + ranking still identical.
"""

import json
from pathlib import Path
from collections import defaultdict
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from pipeline.transform.nlp_utils import (
    clean_text,
    get_embedding,
    sentiment_score,
    cosine_sim,
)

ROOT = Path(__file__).resolve().parents[2]
SILVER_IN = ROOT / "data" / "silver" / "movies_silver_enriched.json"
SILVER_OUT = ROOT / "data" / "silver" / "movies_silver_validated.json"

# thresholds
RELEVANCE_THRESHOLD = 0.62
DUPLICATE_SIM_THRESHOLD = 0.92
MIN_REVIEW_LENGTH = 40
MAX_KEEP_PER_MOVIE = 10


# -------------------------------------------------------------------
# Create keyword set from movie genres
# -------------------------------------------------------------------
def genre_to_keywords(genres):
    kws = []
    for g in genres:
        name = g.get("name") if isinstance(g, dict) else str(g)
        kws.append(name)

        low = name.lower()
        if low == "romance":
            kws += ["love", "relationship", "breakup", "affection"]
        if low in ("drama", "romance"):
            kws += ["emotion", "relationship", "character", "tears", "family"]
        if low in ("action", "adventure"):
            kws += ["fight", "battle", "chase", "explosion", "action"]
        if low in ("science fiction", "sci-fi", "fantasy"):
            kws += ["space", "future", "technology", "alien", "time"]
        if low in ("mystery", "thriller"):
            kws += ["mystery", "twist", "suspense", "reveal"]
        if low == "comedy":
            kws += ["funny", "humor", "laugh", "comedy"]

    # remove dupes, join
    return " . ".join(list(dict.fromkeys(kws)))


# -------------------------------------------------------------------
# NEW OPTIMIZED RELEVANCE FUNCTION
# -------------------------------------------------------------------
def relevance_from_embeddings(review_emb, context_embs, threshold):
    """
    Efficient version of is_relevant:
      - review_emb: vector
      - context_embs: list of vectors
    """
    if review_emb is None:
        return {"score": 0.0, "relevant": False, "best_context_idx": None}

    best_score = 0.0
    best_idx = None

    for i, c_emb in enumerate(context_embs):
        if c_emb is None:
            continue
        score = cosine_sim(review_emb, c_emb)
        if score > best_score:
            best_score = score
            best_idx = i

    return {
        "score": best_score,
        "relevant": best_score >= threshold,
        "best_context_idx": best_idx,
    }


# -------------------------------------------------------------------
# Remove duplicates by embedding
# -------------------------------------------------------------------
def dedupe_by_embedding(review_items):
    kept = []
    embeddings = []

    for r in review_items:
        emb = r.get("embedding")

        if emb is None:
            kept.append(r)
            embeddings.append(None)
            continue

        duplicate = False
        for other_emb in embeddings:
            if other_emb is None:
                continue
            if cosine_sim(emb, other_emb) >= DUPLICATE_SIM_THRESHOLD:
                duplicate = True
                break

        if not duplicate:
            kept.append(r)
            embeddings.append(emb)

    return kept


# -------------------------------------------------------------------
# MAIN MOVIE PROCESSING LOGIC
# -------------------------------------------------------------------
def process_movie(m):
    overview = m.get("overview", "") or ""
    genres = m.get("genres", [])

    # Build context strings
    context_texts = []
    if overview:
        context_texts.append(overview)

    gk = genre_to_keywords(genres)
    if gk:
        context_texts.append(gk)

    # PRE-CALCULATE CONTEXT EMBEDDINGS (big optimization)
    context_embs = []
    for c in context_texts:
        try:
            context_embs.append(get_embedding(c))
        except:
            context_embs.append(None)

    validated_reviews = []
    review_items_for_dedupe = []

    reviews = m.get("reviews", []) or []

    # -------- Review Loop ----------
    for rev in reviews:
        cleaned = clean_text(rev)

        # Too short to be meaningful
        if len(cleaned) < MIN_REVIEW_LENGTH:
            validated_reviews.append({
                "content": cleaned,
                "length": len(cleaned),
                "sentiment": sentiment_score(cleaned),
                "relevance": {"score": 0.0, "relevant": False, "best_context_idx": None},
                "embedding": None,
                "keep": False,
                "reason": "too_short",
            })
            continue

        # Compute review embedding once
        try:
            r_emb = get_embedding(cleaned)
        except:
            r_emb = None

        # Compute relevance using cached context embeddings
        rel = relevance_from_embeddings(
            r_emb,
            context_embs,
            threshold=RELEVANCE_THRESHOLD,
        )

        item = {
            "content": cleaned,
            "length": len(cleaned),
            "sentiment": sentiment_score(cleaned),
            "relevance": rel,
            "embedding": r_emb,
            "keep": None,
            "reason": None
        }

        review_items_for_dedupe.append(item)

    # -------- DEDUPE ----------
    deduped = dedupe_by_embedding(review_items_for_dedupe)

    # -------- RANKING ----------
    ranked = sorted(
        deduped,
        key=lambda x: (
            x["relevance"]["score"],
            x["length"],
            abs(x["sentiment"]["polarity"]),
        ),
        reverse=True,
    )

    keep_set = set()
    for r in ranked[:MAX_KEEP_PER_MOVIE]:
        r["keep"] = True
        r["reason"] = "top_ranked"
        keep_set.add(r["content"])

    for r in deduped:
        if r["content"] not in keep_set:
            r["keep"] = False
            r["reason"] = "low_rank"

    # Combine in original review order
    final = []
    content_to_item = {r["content"]: r for r in deduped}

    for orig in reviews:
        c = clean_text(orig)
        if c in content_to_item:
            final.append(content_to_item[c])
            content_to_item.pop(c, None)

    # Add any leftover deduped items
    for r in deduped:
        if r["content"] not in [v["content"] for v in final]:
            final.append(r)

    return final


# -------------------------------------------------------------------
# MAIN SCRIPT
# -------------------------------------------------------------------
def main():
    with open(SILVER_IN, "r", encoding="utf-8") as f:
        movies = json.load(f)

    print(f"[+] Loaded {len(movies)} movies for validation.")

    validated = []
    missing = 0
    total_reviews = 0
    kept_total = 0

    for m in movies:
        total_reviews += len(m.get("reviews", []))
        if m.get("reviews_missing"):
            missing += 1

        processed = process_movie(m)

        # Remove embeddings before writing output
        for r in processed:
            r.pop("embedding", None)

        kept_total += sum(r["keep"] for r in processed)

        m_out = dict(m)
        m_out["validated_reviews"] = processed
        validated.append(m_out)

    with open(SILVER_OUT, "w", encoding="utf-8") as f:
        json.dump(validated, f, indent=2, ensure_ascii=False)

    print(f"[✓] Saved validated reviews → {SILVER_OUT}")
    print(f"[✓] Movies missing reviews: {missing}")
    print(f"[✓] Total reviews processed: {total_reviews}")
    print(f"[✓] Total keep=True reviews: {kept_total}")


if __name__ == "__main__":
    main()
