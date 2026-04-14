import sqlite3
from app.config import APP_DB
from app.database.db_setup import create_tables


def get_db_connection():
    conn = sqlite3.connect(APP_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_aquarium_module():
    create_tables()


def create_aquarium(name, volume):
    if not name or name.strip() == "":
        return {"success": False, "message": "Akvariumo pavadinimas privalomas."}

    if volume <= 0:
        return {"success": False, "message": "Akvariumo tūris turi būti didesnis už 0."}

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO aquarium (aquarium_name, volume) VALUES (?, ?)",
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

        cursor.execute("SELECT * FROM aquarium")
        aquariums_data = cursor.fetchall()

        aquariums = []

        for aquarium_row in aquariums_data:
            cursor.execute("""
                SELECT 
                    fl.id,
                    fl.fish_name,
                    fl.aggression,
                    fl.size,
                    fl.temp_min,
                    fl.temp_max,
                    fl.ph_min,
                    fl.ph_max
                FROM fish_in_aquarium fia
                JOIN fish_list fl ON fia.fish_id = fl.id
                WHERE fia.aquarium_id = ?
            """, (aquarium_row["id"],))

            fish_data = cursor.fetchall()

            fish_list = [
                {
                    "id": fish["id"],
                    "name": fish["fish_name"],
                    "aggression": fish["aggression"],
                    "size": fish["size"],
                    "temp_min": fish["temp_min"],
                    "temp_max": fish["temp_max"],
                    "ph_min": fish["ph_min"],
                    "ph_max": fish["ph_max"]
                }
                for fish in fish_data
            ]

            aquarium = {
                "id": aquarium_row["id"],
                "name": aquarium_row["aquarium_name"],
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


def add_fish_to_aquarium(aquarium_id, fish_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM aquarium WHERE id = ?", (aquarium_id,))
        if not cursor.fetchone():
            return "Akvariumas nerastas"

        cursor.execute("SELECT id FROM fish_list WHERE id = ?", (fish_id,))
        if not cursor.fetchone():
            return "Žuvis nerasta kataloge"

        cursor.execute("""
            INSERT INTO fish_in_aquarium (aquarium_id, fish_id)
            VALUES (?, ?)
        """, (aquarium_id, fish_id))

        conn.commit()
        return "Žuvis pridėta į akvariumą"

    except sqlite3.Error as e:
        return f"Duomenų bazės klaida: {str(e)}"

    finally:
        if "conn" in locals():
            conn.close()