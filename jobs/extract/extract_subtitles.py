#!/usr/bin/env python3

"""
jobs/test_yts_search.py
Runs the test search function on YTS subtitles.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from pipeline.extract.subtitle_extractor import test_yts_search


def main():
    title = "Inception"
    year = 2010

    print(f"Testing search for: {title} ({year})\n")

    result = test_yts_search(title, year)
    print("Search OK :", result["ok"])
    print("Query     :", result["query"])
    print("Results   :", result["results"])
    print("Error     :", result["error"])


if __name__ == "__main__":
    main()
