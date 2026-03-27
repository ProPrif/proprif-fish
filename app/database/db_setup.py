import sqlite3
from app.config import APP_DB


def create_tables():
    conn = sqlite3.connect(APP_DB)
    cursor = conn.cursor()

    # Aquarium table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS aquarium (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aquarium_name TEXT NOT NULL,
            volume REAL NOT NULL
        )
    """)

    # Fish list / catalog table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fish_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fish_name TEXT NOT NULL,
            aggression TEXT NOT NULL,
            size REAL NOT NULL,
            temp_min REAL NOT NULL,
            temp_max REAL NOT NULL,
            ph_min REAL NOT NULL,
            ph_max REAL NOT NULL
        )
    """)

    # Fish in aquarium (relation table)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fish_in_aquarium (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aquarium_id INTEGER NOT NULL,
            fish_id INTEGER NOT NULL,
            FOREIGN KEY (aquarium_id) REFERENCES aquariums(id) ON DELETE CASCADE,
            FOREIGN KEY (fish_id) REFERENCES fish_list(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()