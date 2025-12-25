import json
import re

BANNED_WORDS = {
    "explores", "reflects", "narrative", "journey", "symbolizes",
    "masterfully", "intricately", "the film", "the movie"
}

def validate_emotional_capsules(text, allowed_axes):
    try:
        capsules = json.loads(text)
    except Exception:
        return False, "invalid_json"

    if not isinstance(capsules, list) or len(capsules) != 4:
        return False, "wrong_count"

    seen_emotions = set()

    for c in capsules:
        if not all(k in c for k in ("axis", "emotion", "text")):
            return False, "missing_fields"

        if c["axis"] not in allowed_axes:
            return False, "invalid_axis"

        emotion = c["emotion"].lower().strip()
        if " " in emotion:
            return False, "emotion_not_single_word"

        if emotion in seen_emotions:
            return False, "duplicate_emotion"
        seen_emotions.add(emotion)

        text_lower = c["text"].lower()

        if len(c["text"].split(".")) > 2:
            return False, "too_many_sentences"

        if any(b in text_lower for b in BANNED_WORDS):
            return False, "ai_language"

        if re.search(r"[A-Z][a-z]+", c["text"]):
            return False, "possible_character_name"

    return True, "pass"
