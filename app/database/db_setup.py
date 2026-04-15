import sqlite3

from app.config import APP_DB


def create_tables() -> None:
    conn = sqlite3.connect(APP_DB)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS aquarium (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aquarium_name TEXT NOT NULL,
            volume REAL NOT NULL
        )
        """
    )

    cursor.execute(
        """
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
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS fish_in_aquarium (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aquarium_id INTEGER NOT NULL,
            fish_id INTEGER NOT NULL,
            FOREIGN KEY (aquarium_id) REFERENCES aquarium(id) ON DELETE CASCADE,
            FOREIGN KEY (fish_id) REFERENCES fish_list(id) ON DELETE CASCADE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS compatibility_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            aquarium_id INTEGER,
            aquarium_name TEXT,
            fish_names TEXT NOT NULL,
            result TEXT NOT NULL,
            FOREIGN KEY (aquarium_id) REFERENCES aquarium(id) ON DELETE SET NULL
        )
        """
    )

    conn.commit()
    conn.close()
