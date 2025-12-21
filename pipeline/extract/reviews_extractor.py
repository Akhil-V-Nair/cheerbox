import os
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv
from requests.exceptions import RequestException

load_dotenv()
TMDB_KEY = os.getenv("TMDB_BEARER_TOKEN")

BASE_URL = "https://api.themoviedb.org/3"

HEADERS = {
    "Authorization": f"Bearer {TMDB_KEY}",
    "Content-Type": "application/json;charset=utf-8"
}


class ReviewExtractor:
    def __init__(self, save_dir):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------
    # INTERNAL METHOD: Safe request with retry + backoff
    # ------------------------------------------------------------
    def _request_with_retry(self, url, max_retries=6):
        delay = 1

        for attempt in range(1, max_retries + 1):
            try:
                resp = requests.get(url, headers=HEADERS, timeout=10)

                # TMDB rate-limit (rarely returns 429, but handle anyway)
                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", 3))
                    print(f"   [429] Rate limited → waiting {retry_after}s")
                    time.sleep(retry_after)
                    continue

                resp.raise_for_status()
                return resp.json()

            except RequestException as e:
                print(f"   ⚠ Request failed (attempt {attempt}/{max_retries}): {e}")
                time.sleep(delay)
                delay = min(delay * 2, 15)  # exponential backoff but capped

        print("   ❌ All retries failed — skipping movie.")
        return None

    # ------------------------------------------------------------
    # Public method: Fetch reviews
    # ------------------------------------------------------------
    def fetch_reviews(self, movie_id):
        """Fetch TMDB reviews for a movie."""
        url = f"{BASE_URL}/movie/{movie_id}/reviews"
        print(f"   TMDB Reviews URL: {url}")

        data = self._request_with_retry(url)
        if not data:
            return []

        results = data.get("results", [])
        cleaned = []

        for r in results:
            cleaned.append({
                "rating": r.get("author_details", {}).get("rating"),
                "content": r.get("content", "").strip(),
            })

        return cleaned

    # ------------------------------------------------------------
    # Save reviews to disk
    # ------------------------------------------------------------
    def save(self, movie_id, reviews):
        out = self.save_dir / f"{movie_id}.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(reviews, f, indent=2, ensure_ascii=False)
        return out
