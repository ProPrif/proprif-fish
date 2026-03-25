import sqlite3
from app.config import APP_DB
from app.database.aquarium_db_setup import create_aquarium_tables


def get_db_connection():
    conn = sqlite3.connect(APP_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_aquarium_module():
    create_aquarium_tables()


def create_aquarium(name, volume):
    if not name or name.strip() == "":
        return {"success": False, "message": "Akvariumo pavadinimas privalomas."}

    if volume <= 0:
        return {"success": False, "message": "Akvariumo tūris turi būti didesnis už 0."}

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO aquariums (name, volume) VALUES (?, ?)",
            (name, volume)
        )
        aquarium_id = cursor.lastrowid
        conn.commit()

        aquarium = {
            "id": aquarium_id,
            "name": name,
            "volume": volume,
            "fish": []
        }

        return {
            "success": True,
            "message": "Akvariumas sėkmingai sukurtas.",
            "aquarium": aquarium
        }

    except sqlite3.Error as e:
        return {"success": False, "message": f"Duomenų bazės klaida: {str(e)}"}

    finally:
        if "conn" in locals():
            conn.close()


def get_all_aquariums():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM aquariums")
        aquariums_data = cursor.fetchall()

        aquariums = []
        for aquarium_row in aquariums_data:
            cursor.execute(
                "SELECT name, size FROM aquarium_fish WHERE aquarium_id = ?",
                (aquarium_row["id"],)
            )
            fish_data = cursor.fetchall()

            fish_list = [
                {"name": fish["name"], "size": fish["size"]}
                for fish in fish_data
            ]

            aquarium = {
                "id": aquarium_row["id"],
                "name": aquarium_row["name"],
                "volume": aquarium_row["volume"],
                "fish": fish_list
            }
            aquariums.append(aquarium)

        return aquariums

    except sqlite3.Error as e:
        print(f"Duomenų bazės klaida: {str(e)}")
        return []

    finally:
        if "conn" in locals():
            conn.close()


def add_fish_to_aquarium(aquarium_id, fish_name, size):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM aquariums WHERE id = ?", (aquarium_id,))
        if not cursor.fetchone():
            return "Akvariumas nerastas"

        cursor.execute(
            "INSERT INTO aquarium_fish (aquarium_id, name, size) VALUES (?, ?, ?)",
            (aquarium_id, fish_name, size)
        )
        conn.commit()

        return "Žuvis pridėta"

    except sqlite3.Error as e:
        return f"Duomenų bazės klaida: {str(e)}"

    finally:
        if "conn" in locals():
            conn.close()