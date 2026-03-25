import sqlite3
from app.config import APP_DB


def create_fish_table():
    conn = sqlite3.connect(APP_DB)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS fish_catalog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            temperature REAL NOT NULL,
            aggression TEXT NOT NULL,
            size REAL NOT NULL
        )
    """)

    conn.commit()
    conn.close()