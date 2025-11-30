#!/usr/bin/env python3
"""
Sets up DuckDB database (cheerbox.db) from Gold Parquet files.

Creates:
- movies
- genres
- movie_genres
- movie_source_categories
"""

import duckdb
from pathlib import Path

# -------------------------------------------------------------
# Resolve paths
# -------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
GOLD_DIR = ROOT / "data" / "gold"
DB_PATH = ROOT / "cheerbox.db"

# -------------------------------------------------------------
# DDL statements (table schema)
# -------------------------------------------------------------
DDL_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS movies (
        movie_id INTEGER PRIMARY KEY,
        imdb_id TEXT,
        title TEXT,
        overview TEXT,
        poster_path TEXT,
        vote_count INTEGER,
        vote_average DOUBLE,
        popularity DOUBLE
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS genres (
        genre_id INTEGER PRIMARY KEY,
        genre_name TEXT
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS movie_genres (
        movie_id INTEGER,
        genre_id INTEGER,
        FOREIGN KEY(movie_id) REFERENCES movies(movie_id),
        FOREIGN KEY(genre_id) REFERENCES genres(genre_id)
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS movie_source_categories (
        movie_id INTEGER,
        source_category TEXT,
        FOREIGN KEY(movie_id) REFERENCES movies(movie_id)
    );
    """
]


# -------------------------------------------------------------
# Load Parquet → DuckDB table
# -------------------------------------------------------------
def load_table(con, table_name, parquet_file):
    print(f"[+] Loading {table_name} from {parquet_file.name} ...")

    con.execute(f"DELETE FROM {table_name};")
    con.execute(f"""
        INSERT INTO {table_name}
        SELECT * FROM '{parquet_file}';
    """)

    count = con.execute(f"SELECT COUNT(*) FROM {table_name};").fetchone()[0]
    print(f"    → {count} rows loaded.\n")


# -------------------------------------------------------------
# Main
# -------------------------------------------------------------
def main():
    print("[*] Initializing DuckDB...")

    con = duckdb.connect(str(DB_PATH))
    print(f"[+] Connected to: {DB_PATH}")

    # Create schema
    print("[*] Creating tables...")
    for ddl in DDL_STATEMENTS:
        con.execute(ddl)

    # Load tables
    load_table(con, "movies", GOLD_DIR / "movies.parquet")
    load_table(con, "genres", GOLD_DIR / "genres.parquet")
    load_table(con, "movie_genres", GOLD_DIR / "movie_genres.parquet")
    load_table(con, "movie_source_categories",
               GOLD_DIR / "movie_source_categories.parquet")

    print("[✓] DuckDB setup complete!")
    con.close()


if __name__ == "__main__":
    main()
