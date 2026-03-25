import sqlite3
from app.config import APP_DB


def create_aquarium_tables():
    conn = sqlite3.connect(APP_DB)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS aquariums (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            volume REAL NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS aquarium_fish (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aquarium_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            size REAL NOT NULL,
            FOREIGN KEY (aquarium_id) REFERENCES aquariums(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()