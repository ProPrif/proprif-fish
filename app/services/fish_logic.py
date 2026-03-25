import sqlite3
from app.config import APP_DB
from app.database.fish_db_setup import create_fish_table


def get_db_connection():
    conn = sqlite3.connect(APP_DB)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_fish_module():
    create_fish_table()


def add_fish(name, temperature, aggression, size):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO fish_catalog (name, temperature, aggression, size)
            VALUES (?, ?, ?, ?)
        """, (name, temperature, aggression, size))

        conn.commit()

        cursor.execute("""
            SELECT * FROM fish_catalog
            WHERE name = ? AND temperature = ? AND aggression = ? AND size = ?
            ORDER BY id DESC
            LIMIT 1
        """, (name, temperature, aggression, size))

        result = cursor.fetchone()

        if result:
            return dict(result)

        return None

    except sqlite3.Error as e:
        print(f"Duomenų bazės klaida: {str(e)}")
        return None

    finally:
        if "conn" in locals():
            conn.close()


def get_all_fish():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM fish_catalog ORDER BY id")
        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    except sqlite3.Error as e:
        print(f"Duomenų bazės klaida: {str(e)}")
        return []

    finally:
        if "conn" in locals():
            conn.close()


def clear_fish_table():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM fish_catalog")
        conn.commit()

    except sqlite3.Error as e:
        print(f"Duomenų bazės klaida: {str(e)}")

    finally:
        if "conn" in locals():
            conn.close()