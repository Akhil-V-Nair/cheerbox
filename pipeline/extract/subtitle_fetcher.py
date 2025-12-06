import os
import time
import json
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin


class SubtitleFetcher:
    """
    Robust SubtitleFetcher for yifysubtitles.org (YTS Subs).
    Save raw SRT to save_dir/<movie_id>.srt and return metadata + text.
    """

    BASE_URL = "https://yifysubtitles.org/movie-imdb/"

    def __init__(self, save_dir: str, throttle: float = 0.6, verbose: bool = True):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.throttle = throttle
        self.verbose = verbose

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            )
        }
        self.session = requests.Session()
        self.session.headers.update(headers)

    # ----------------------------------------------------------
    def fetch_page(self, imdb_id: str):
        """Download the HTML subtitle listing page."""
        url = f"{self.BASE_URL}{imdb_id}"
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code == 404:
                return None, "Page not found (404)"
            resp.raise_for_status()
            return resp.text, None
        except Exception as e:
            return None, str(e)

    # ----------------------------------------------------------
    def resolve_detail_download(self, detail_url: str):
        """
        Some subtitle links lead to a detail page. Fetch that page and
        try to locate a direct .srt download link or an explicit download button.
        """
        try:
            resp = self.session.get(detail_url, timeout=12)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Look for direct .srt links first
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.lower().endswith(".srt"):
                    return urljoin(detail_url, href)

            # Look for buttons/links that contain 'download' in class or text
            for a in soup.find_all("a", href=True):
                txt = (a.get_text() or "").strip().lower()
                cls = " ".join(a.get("class") or []).lower()
                if "download" in txt or "download" in cls:
                    return urljoin(detail_url, a["href"])

            return None
        except Exception:
            return None

    # ----------------------------------------------------------
    def parse_english_sub_url(self, html: str):
        """
        More tolerant parser:
        - find rows/entries that look like subtitle entries
        - for each candidate, check whether it is English (by nearby text)
        - return direct .srt URL if available or a detail page URL to be resolved
        """
        soup = BeautifulSoup(html, "html.parser")

        # Strategy A: find rows with class or structure used for subtitle entries
        # Try several selectors to be resilient.
        candidate_rows = soup.select("tr.subtitle-entry, tr") or soup.find_all("tr")

        for row in candidate_rows:
            try:
                row_text = row.get_text(separator=" ").strip().lower()

                # Quick skip if no english word
                if "english" not in row_text:
                    continue

                # Find possible anchor(s) in this row
                anchors = row.find_all("a", href=True)
                for a in anchors:
                    href = a["href"]
                    # Many hrefs are relative paths
                    full_href = urljoin("https://yifysubtitles.org", href)

                    # If anchor points directly to .srt
                    if href.lower().endswith(".srt"):
                        return full_href

                    # If anchor is a subtitle detail page (contains /subtitle/), try resolve
                    if "/subtitle/" in href or "/subtitle-download" in href:
                        resolved = self.resolve_detail_download(full_href)
                        if resolved:
                            return resolved
                        # fallback to the detail page itself as last resort
                        return full_href

                # Also check for any link in row that points to '/subtitle/'
                for a in row.select("a[href*='/subtitle/']"):
                    href = a["href"]
                    full_href = urljoin("https://yifysubtitles.org", href)
                    resolved = self.resolve_detail_download(full_href)
                    if resolved:
                        return resolved
                    return full_href
            except Exception:
                continue

        # Strategy B: site may present subtitle links as direct list anchors elsewhere
        for a in soup.find_all("a", href=True):
            txt = (a.get_text() or "").strip().lower()
            # anchor text may include language info like 'English (United States)'
            if "english" in txt and (".srt" in a["href"] or "/subtitle/" in a["href"]):
                return urljoin("https://yifysubtitles.org", a["href"])

        return None

    # ----------------------------------------------------------
    def download_srt(self, url: str, movie_id: int):
        """Download the SRT file and save it to save_dir/<movie_id>.srt"""
        try:
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()

            # If the response is HTML (not direct srt), try to find a .srt link inside
            content_type = resp.headers.get("Content-Type", "")
            if "text/html" in content_type and ".srt" in resp.text:
                # try to extract srt link from the HTML we've got
                soup = BeautifulSoup(resp.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if href.lower().endswith(".srt"):
                        url = urljoin(url, href)
                        resp = self.session.get(url, timeout=15)
                        resp.raise_for_status()
                        break

            file_path = self.save_dir / f"{movie_id}.srt"
            with open(file_path, "wb") as f:
                f.write(resp.content)

            return str(file_path), None

        except Exception as e:
            return None, str(e)

    # ----------------------------------------------------------
    def fetch_subtitle(self, movie_id: int, imdb_id: str):
        """
        Main method.
        Returns:
            metadata: dict
            srt_text: str or None
        """
        if self.verbose:
            print(f"→ Fetching subtitles for {movie_id} ({imdb_id})")

        metadata = {
            "movie_id": movie_id,
            "imdb_id": imdb_id,
            "subtitle_source": "yts",
            "found": False,
            "download_url": None,
            "file_path": None,
            "error": None,
        }

        # Step 1 — fetch HTML page
        html, error = self.fetch_page(imdb_id)
        if error:
            metadata["error"] = error
            return metadata, None

        if self.verbose:
            # quick debug hint: length of HTML
            print(f"  [debug] page length: {len(html)} characters")

        # Step 2 — extract English subtitle download URL
        sub_url = self.parse_english_sub_url(html)
        if not sub_url:
            metadata["error"] = "No English subtitle found"
            return metadata, None

        metadata["download_url"] = sub_url

        # Step 3 — download SRT file
        file_path, error = self.download_srt(sub_url, movie_id)
        if error:
            metadata["error"] = error
            return metadata, None

        metadata["file_path"] = file_path
        metadata["found"] = True

        # Return raw subtitle text
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception:
            text = None

        time.sleep(self.throttle)  # be polite
        return metadata, text
