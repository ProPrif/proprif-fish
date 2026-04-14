import sqlite3
from pathlib import Path
import sys

try:
    from app.config import APP_DB
    from app.database.db_setup import create_tables
except ModuleNotFoundError:
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from app.config import APP_DB
    from app.database.db_setup import create_tables

def get_connection():
    return sqlite3.connect(APP_DB)


def ensure_tables():
    create_tables()


def search_fish(search_text):
    ensure_tables()
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT id, fish_name, aggression, size
        FROM fish_list
        WHERE fish_name LIKE ?
    """

    cursor.execute(query, ('%' + search_text + '%',))
    fish = cursor.fetchall()

    conn.close()

    return fish

def add_fish_to_aquarium(aquarium_id, fish_id, quantity):
    # Validacija
    if quantity <= 0:
        return {"error": "Kiekis turi būti > 0"}

    conn = get_connection()
    cursor = conn.cursor()

    # Patikrinam ar žuvis egzistuoja
    cursor.execute("SELECT id FROM fish_list WHERE id = ?", (fish_id,))
    fish = cursor.fetchone()

    if not fish:
        conn.close()
        return {"error": "Žuvis nerasta"}

    # Įrašome tiek eilučių, koks kiekis
    for _ in range(quantity):
        cursor.execute("""
            INSERT INTO fish_in_aquarium (aquarium_id, fish_id)
            VALUES (?, ?)
        """, (aquarium_id, fish_id))

    conn.commit()
    conn.close()

    return {"success": True}

def get_aquarium_fish(aquarium_id):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT fish_list.fish_name, COUNT(fish_in_aquarium.fish_id) as quantity
        FROM fish_in_aquarium
        JOIN fish_list ON fish_in_aquarium.fish_id = fish_list.id
        WHERE fish_in_aquarium.aquarium_id = ?
        GROUP BY fish_in_aquarium.fish_id
    """

    cursor.execute(query, (aquarium_id,))
    result = cursor.fetchall()

    conn.close()
    return result

if __name__ == "__main__":
    pass