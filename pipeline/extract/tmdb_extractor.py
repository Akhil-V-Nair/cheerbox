import json
import os
import requests
import time
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BEARER_TOKEN = os.getenv("TMDB_BEARER_TOKEN")

# Resolve project root safely (3 levels up)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
BRONZE_DIR = os.path.join(BASE_DIR, "data", "bronze")


# =====================
# TMDB API CLIENT
# =====================

class TMDBClient:
    """
    Responsible ONLY for making TMDb API requests.
    Clean, low-level HTTP wrapper.
    """

    BASE_URL = "https://api.themoviedb.org/3"

    def __init__(self, bearer_token: str):
        if not bearer_token:
            raise ValueError("TMDB_BEARER_TOKEN not found in .env file.")
        
        self.headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json;charset=utf-8"
        }

    def get_genres(self) -> Dict:
        """Fetch TMDb genre list."""
        url = f"{self.BASE_URL}/genre/movie/list"
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def discover_movies(self, genre_id: int, page: int = 1) -> Dict:
        """Fetch movies for a genre + page number."""
        url = f"{self.BASE_URL}/discover/movie"
        params = {
            "with_genres": genre_id,
            "page": page,
            "language": "en-US",
            "sort_by": "vote_average.desc",
            "vote_count.gte": 5000
        }

        r = requests.get(url, headers=self.headers, params=params)
        r.raise_for_status()
        return r.json()


# =====================
# EXTRACTOR CLASS
# =====================

class MovieExtractor:
    """
    Uses TMDBClient to:
    - Fetch top movies (up to 1000)
    - Filter English movies
    - Save raw dumps to bronze layer
    """

    def __init__(self, tmdb_client: TMDBClient, bronze_path: str = BRONZE_DIR, verbose: bool = True):
        self.tmdb = tmdb_client
        self.bronze_path = bronze_path
        self.verbose = verbose

    # ---------------------
    # GENRE RESOLUTION
    # ---------------------
    def resolve_genre_ids(self, target_genres: Dict[str, List[str]]) -> Dict[str, List[int]]:
        """ Map genre names → TMDb genre IDs dynamically. """

        tmdb_genres = self.tmdb.get_genres().get("genres", [])
        resolved = {}

        for label, genre_names in target_genres.items():
            ids = [
                g["id"]
                for g in tmdb_genres
                if g["name"] in genre_names
            ]
            resolved[label] = ids

        return resolved

    # ---------------------
    # MOVIE EXTRACTION
    # ---------------------
    def fetch_top_movies_for_genre(self, genre_id: int, limit: int = 1000) -> List[Dict]:
        """Fetch up to 1000 movies safely."""
        movies = []
        page = 1
        max_pages = 500  # TMDb API limit

        while len(movies) < limit and page <= max_pages:
            if self.verbose:
                print(f"[Genre {genre_id}] Fetching page {page}...")

            data = self.tmdb.discover_movies(genre_id, page)
            results = data.get("results", [])

            if not results:
                break

            for m in results:
                if len(movies) >= limit:
                    break

                if m.get("original_language") != "en":
                    continue

                movie_info = {
                    "movie_id": m["id"],
                    "title": m["title"],
                    "overview": m.get("overview", ""),
                    "vote_average": m.get("vote_average"),
                    "vote_count": m.get("vote_count"),
                    "popularity": m.get("popularity"),
                    "poster_path": m.get("poster_path"),
                    "genre_id": genre_id
                }

                movies.append(movie_info)

            page += 1
            time.sleep(0.3)  # Prevent rate-limit

        return movies

    # ---------------------
    # SAVE RAW OUTPUT
    # ---------------------
    def save_raw_movies(self, genre_name: str, movies: List[Dict]):
        os.makedirs(self.bronze_path, exist_ok=True)
        filepath = os.path.join(self.bronze_path, f"{genre_name}_raw.json")

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(movies, f, indent=2)

        print(f"[+] Saved {len(movies)} movies → {filepath}")


