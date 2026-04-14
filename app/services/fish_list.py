import sqlite3
from app.config import APP_DB
from datetime import datetime


def _history_has_column(column_name: str) -> bool:
    conn = sqlite3.connect(APP_DB)
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(compatibility_history)")
        columns = {row[1] for row in cursor.fetchall()}
        return column_name in columns
    finally:
        conn.close()


def save_to_history(selected_fish, result, aquarium_id=None, aquarium_name=None):
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fish_names = [fish["name"] for fish in selected_fish]

    conn = sqlite3.connect(APP_DB)
    cursor = conn.cursor()

    if aquarium_name is not None and not _history_has_column("aquarium_name"):
        cursor.execute("ALTER TABLE compatibility_history ADD COLUMN aquarium_name TEXT")

    if _history_has_column("aquarium_name"):
        cursor.execute(
            """
            INSERT INTO compatibility_history (timestamp, aquarium_id, aquarium_name, fish_names, result)
            VALUES (?, ?, ?, ?, ?)
            """,
            (time, aquarium_id, aquarium_name, ", ".join(fish_names), result),
        )
    else:
        cursor.execute(
            """
            INSERT INTO compatibility_history (timestamp, aquarium_id, fish_names, result)
            VALUES (?, ?, ?, ?)
            """,
            (time, aquarium_id, ", ".join(fish_names), result),
        )

    conn.commit()
    conn.close()


def get_history_entries(limit=10):
    conn = sqlite3.connect(APP_DB)
    cursor = conn.cursor()

    if _history_has_column("aquarium_name"):
        cursor.execute(
            """
            SELECT ch.id,
                   ch.timestamp,
                   COALESCE(ch.aquarium_name, a.aquarium_name) AS aquarium_name,
                   ch.fish_names,
                   ch.result
            FROM compatibility_history ch
            LEFT JOIN aquarium a ON a.id = ch.aquarium_id
            ORDER BY ch.timestamp DESC
            LIMIT ?
            """,
            (limit,),
        )
    else:
        cursor.execute(
            """
            SELECT ch.id,
                   ch.timestamp,
                   a.aquarium_name,
                   ch.fish_names,
                   ch.result
            FROM compatibility_history ch
            LEFT JOIN aquarium a ON a.id = ch.aquarium_id
            ORDER BY ch.timestamp DESC
            LIMIT ?
            """,
            (limit,),
        )

    history_entries = cursor.fetchall()
    conn.close()
    return history_entries


def delete_history_entry_db(entry_id):
    if entry_id is None:
        return False

    conn = sqlite3.connect(APP_DB)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM compatibility_history WHERE id = ?", (entry_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted
