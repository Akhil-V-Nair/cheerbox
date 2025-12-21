"""
nlp_utils.py

Provides:
- Embedding generation (via LLM API or a local fallback)
- Cosine similarity
- Relevance scoring between review text and movie context
- Lightweight sentiment analysis fallback
"""

import os
import math
import numpy as np
from typing import List, Dict, Optional
from dotenv import load_dotenv
import unicodedata
import re

load_dotenv()
_re_html = re.compile(r"<[^>]+>")
_re_whitespace = re.compile(r"\s+")
# NEW: Regex to match ALL C0 and C1 control characters (non-printing/ambiguous)
_re_control_chars = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]')

# -------------------------------------------------------------------
# Embedding Provider (LLM API)
# -------------------------------------------------------------------

USE_REMOTE_EMBEDDING = False

def clean_text(text: str) -> str:
    if not text:
        return ""
    
    # 1. Unicode Normalization: Converts complex characters into canonical forms.
    # This addresses many ambiguous character issues immediately.
    t = unicodedata.normalize('NFKD', text)

    # 2. Control Character Stripping: Removes non-printing/ambiguous characters.
    t = _re_control_chars.sub("", t)

    # 3. HTML/Tag Stripping
    t = _re_html.sub(" ", t)

    # 4. Collapse all remaining whitespace (including newlines and multiple spaces)
    t = _re_whitespace.sub(" ", t)
    
    return t.strip()


def get_embedding_remote(text: str) -> Optional[List[float]]:
    """
    Calls the remote embedding model (OpenAI / compatible).
    Returns None if the request fails.
    """
    try:
        from openai import OpenAI
        client = OpenAI()

        text = text[:3500]  # safety truncation for remote models

        resp = client.embeddings.create(
            model="text-embedding-3-large",
            input=text
        )
        return resp.data[0].embedding
    
    except Exception as e:
        print(f"[Embedding Error] Remote call failed: {e}")
        return None


# -------------------------------------------------------------------
# Local embedding fallback (sentence transformers)
# -------------------------------------------------------------------

_local_model = None

def get_embedding_local(text: str) -> Optional[List[float]]:
    """
    Uses a lightweight local model (mpnet) for embeddings.
    Only loaded once.
    """
    global _local_model

    try:
        if _local_model is None:
            from sentence_transformers import SentenceTransformer
            _local_model = SentenceTransformer("all-mpnet-base-v2")

        text = text[:3500]
        emb = _local_model.encode(text)
        return emb.tolist()

    except Exception as e:
        print(f"[Embedding Error] Local model failed: {e}")
        return None


# -------------------------------------------------------------------
# Unified Embedding API
# -------------------------------------------------------------------

def get_embedding(text: str) -> Optional[List[float]]:
    """
    Returns a vector embedding for a text.
    Automatically chooses remote API or local model.
    """
    if not text or not text.strip():
        return None

    if USE_REMOTE_EMBEDDING:
        emb = get_embedding_remote(text)
        if emb is not None:
            return emb

    # fallback to local
    return get_embedding_local(text)


# -------------------------------------------------------------------
# Cosine Similarity
# -------------------------------------------------------------------

def cosine_sim(a: List[float], b: List[float]) -> float:
    """
    Computes cosine similarity between two embedding vectors.
    Uses NumPy for speed.
    """
    try:
        a = np.array(a, dtype=float)
        b = np.array(b, dtype=float)
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)
    except Exception:
        return 0.0


# -------------------------------------------------------------------
# Relevance Scoring (patched, efficient, precomputed contexts)
# -------------------------------------------------------------------

def is_relevant(
    review_emb: List[float],
    context_embs: List[List[float]],
    threshold: float = 0.62
) -> Dict:
    """
    Determines whether a review is relevant to the movie context.

    review_emb: embedding of the review text (already computed)
    context_embs: list of PRE-COMPUTED embeddings for:
        - overview
        - genre keywords
        - optional: tagline, theme words, etc.

    Returns:
        {
            "score": float,
            "relevant": bool,
            "best_context_idx": int or None
        }
    """

    if review_emb is None or not context_embs:
        return {"score": 0.0, "relevant": False, "best_context_idx": None}

    best_score = -1.0
    best_idx = None

    for i, c_emb in enumerate(context_embs):
        s = cosine_sim(review_emb, c_emb)
        if s > best_score:
            best_score = s
            best_idx = i

    return {
        "score": float(best_score),
        "relevant": best_score >= threshold,
        "best_context_idx": best_idx
    }


# -------------------------------------------------------------------
# Improved Sentiment Fallback
# -------------------------------------------------------------------

try:
    from textblob import TextBlob
    _has_textblob = True
except ImportError:
    _has_textblob = False


def sentiment_score(text: str) -> Dict[str, float]:
    """
    Returns sentiment polarity + subjectivity.
    Falls back to a custom rule-based model if TextBlob is unavailable.
    """

    text = text.strip()
    if not text:
        return {"polarity": 0.0, "subjectivity": 0.0}

    # Try TextBlob first
    if _has_textblob:
        try:
            tb = TextBlob(text)
            return {"polarity": float(tb.sentiment.polarity),
                    "subjectivity": float(tb.sentiment.subjectivity)}
        except Exception:
            pass

    # ---------------------------
    # Lightweight fallback model
    # ---------------------------

    text_lower = text.lower()
    words = text_lower.split()

    pos = ["good", "great", "amazing", "love", "loved", "excellent",
           "best", "enjoy", "funny", "beautiful", "powerful"]
    neg = ["bad", "worst", "hate", "awful", "boring", "disappoint",
           "dull", "terrible", "poor", "annoying", "weak"]

    negation = ["not", "never", "no", "isn't", "wasn't", "don't", "won't"]

    score = 0

    for i, word in enumerate(words):
        is_negated = (i > 0 and words[i-1] in negation)

        if word in pos:
            score += -1 if is_negated else 1

        if word in neg:
            score += 1 if is_negated else -1

    # Normalize score to [-1, 1]
    polarity = max(-1.0, min(1.0, score / max(len(words), 1)))

    return {"polarity": polarity, "subjectivity": 0.5}
