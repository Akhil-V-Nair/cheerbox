import json
import os
import requests
import time
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BEARER_TOKEN = os.getenv("TMDB_BEARER_TOKEN")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
BRONZE_DIR = os.path.join(BASE_DIR, "data", "bronze")


# =====================
# TMDB CLIENT
# =====================

class TMDBClient:
    BASE_URL = "https://api.themoviedb.org/3"

    def __init__(self, bearer_token: str):
        if not bearer_token:
            raise ValueError("TMDB_BEARER_TOKEN missing.")
        
        self.headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json;charset=utf-8"
        }

    def get_genres(self) -> List[Dict]:
        url = f"{self.BASE_URL}/genre/movie/list"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        return resp.json().get("genres", [])

    def discover_movies(self, genre_id: int, page: int = 1) -> Dict:
        url = f"{self.BASE_URL}/discover/movie"
        params = {
            "with_genres": genre_id,
            "page": page,
            "language": "en-US",
            "sort_by": "vote_average.desc",
            "vote_count.gte": 5000
        }
        resp = requests.get(url, headers=self.headers, params=params)
        resp.raise_for_status()
        return resp.json()

    def get_external_ids(self, movie_id: int) -> Dict:
        url = f"{self.BASE_URL}/movie/{movie_id}/external_ids"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def get_movie_details(self, movie_id: int) -> Dict:
        """Real genre list comes from this call."""
        url = f"{self.BASE_URL}/movie/{movie_id}"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        return resp.json()


# =====================
# MOVIE EXTRACTOR
# =====================

class MovieExtractor:
    def __init__(self, tmdb_client: TMDBClient, bronze_path: str = BRONZE_DIR, verbose: bool = True):
        self.tmdb = tmdb_client
        self.bronze_path = bronze_path
        self.verbose = verbose

    def resolve_genre_ids(self, target_genres: Dict[str, List[str]]) -> Dict[str, List[Dict]]:
        """Map your category → TMDb genre objects."""
        tmdb_genres = self.tmdb.get_genres()
        resolved = {}
        for label, names in target_genres.items():
            resolved[label] = [
                {"id": g["id"], "name": g["name"]}
                for g in tmdb_genres
                if g["name"] in names
            ]
        return resolved

    # --------------------------------------------------------
    # FAST FETCH (NO IMDB, NO REAL GENRE LIST YET)
    # --------------------------------------------------------
    def fetch_movies_basic(self, genre_info: Dict, limit: int = 1000, source_category: str = "") -> List[Dict]:
        gid = genre_info["id"]
        gname = genre_info["name"]

        movies = []
        page = 1

        while len(movies) < limit and page <= 500:
            if self.verbose:
                print(f"[{source_category}] Discover {gname} | Page {page}")

            data = self.tmdb.discover_movies(gid, page)
            results = data.get("results", [])
            if not results:
                break

            for m in results:
                if len(movies) >= limit:
                    break
                if m.get("original_language") != "en":
                    continue

                movies.append({
                    "movie_id": m["id"],
                    "title": m["title"],
                    "overview": m.get("overview", ""),
                    "vote_average": m.get("vote_average"),
                    "vote_count": m.get("vote_count"),
                    "popularity": m.get("popularity"),
                    "poster_path": m.get("poster_path"),
                    "source_category": source_category,    # <-- keep track for later
                })

            page += 1
            time.sleep(0.10)

        return movies

    # --------------------------------------------------------
    # FIX: FETCH REAL TMDB GENRE LIST FROM /movie/{id}
    # --------------------------------------------------------
    def attach_real_genres(self, movies: List[Dict]) -> List[Dict]:
        for m in movies:
            mid = m["movie_id"]
            details = self.tmdb.get_movie_details(mid)
            m["genres"] = details.get("genres", [])
            time.sleep(0.10)
        return movies

    # --------------------------------------------------------
    # ATTACH IMDB IDs
    # --------------------------------------------------------
    def attach_imdb_ids(self, movies: List[Dict]) -> List[Dict]:
        imdb_cache = {}

        for m in movies:
            mid = m["movie_id"]

            if mid in imdb_cache:
                m["imdb_id"] = imdb_cache[mid]
                continue

            ext = self.tmdb.get_external_ids(mid)
            imdb_id = ext.get("imdb_id")
            m["imdb_id"] = imdb_id
            imdb_cache[mid] = imdb_id

            time.sleep(0.10)

        return movies

    # --------------------------------------------------------
    def save_raw_movies(self, label: str, movies: List[Dict]):
        os.makedirs(self.bronze_path, exist_ok=True)
        filepath = os.path.join(self.bronze_path, f"{label}_raw.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(movies, f, indent=2)
        print(f"[+] Saved {len(movies)} → {filepath}")
