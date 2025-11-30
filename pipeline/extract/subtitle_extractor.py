import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin

HEADERS = {
    "User-Agent": "cheerbox-search-test/1.0"
}

SEARCH_BASE = "https://yifysubtitles.org/search?q="

def test_yts_search(title: str, year: int = None, max_results: int = 5) -> dict:
    """
    Test YTS search for a given movie title.
    Returns:
      - ok: whether search succeeded
      - results: list of movie page URLs found
      - error: any error string
    """
    result = {
        "ok": False,
        "query": f"{title} {year}" if year else title,
        "results": [],
        "error": None
    }

    try:
        q = f"{title} {year}" if year else title
        url = SEARCH_BASE + quote_plus(q)

        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            result["error"] = f"HTTP {r.status_code}"
            return result

        soup = BeautifulSoup(r.text, "html.parser")

        # Find links to movie pages
        candidates = []
        for a in soup.select("a[href]"):
            href = a["href"]
            if "/movie/" in href or "/movie-imdb/" in href:
                full = urljoin("https://yifysubtitles.org", href)
                if full not in candidates:
                    candidates.append(full)
                if len(candidates) >= max_results:
                    break

        result["results"] = candidates
        result["ok"] = True
        return result

    except Exception as e:
        result["error"] = str(e)
        return result
