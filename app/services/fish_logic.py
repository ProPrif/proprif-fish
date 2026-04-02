import sqlite3
from app.config import APP_DB
from app.database.db_setup import create_tables


def get_db_connection():
    conn = sqlite3.connect(APP_DB)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_fish_module():
    create_tables()


def add_fish(fish_name, aggression, size, temp_min, temp_max, ph_min, ph_max):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO fish_list (
                fish_name,
                aggression,
                size,
                temp_min,
                temp_max,
                ph_min,
                ph_max
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (fish_name, aggression, size, temp_min, temp_max, ph_min, ph_max))

        conn.commit()

        cursor.execute("""
            SELECT * FROM fish_list
            WHERE fish_name = ?
              AND aggression = ?
              AND size = ?
              AND temp_min = ?
              AND temp_max = ?
              AND ph_min = ?
              AND ph_max = ?
            ORDER BY id DESC
            LIMIT 1
        """, (fish_name, aggression, size, temp_min, temp_max, ph_min, ph_max))

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

        cursor.execute("SELECT * FROM fish_list ORDER BY id")
        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    except sqlite3.Error as e:
        print(f"Duomenų bazės klaida: {str(e)}")
        return []

    finally:
        if "conn" in locals():
            conn.close()


def get_fish_by_id(fish_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM fish_list
            WHERE id = ?
        """, (fish_id,))

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


def get_fish_parameters():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT fish_name, aggression, size, temp_min, temp_max, ph_min, ph_max
            FROM fish_list
            ORDER BY id
        """)
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

        cursor.execute("DELETE FROM fish_list")
        conn.commit()

    except sqlite3.Error as e:
        print(f"Duomenų bazės klaida: {str(e)}")

    finally:
        if "conn" in locals():
            conn.close()
