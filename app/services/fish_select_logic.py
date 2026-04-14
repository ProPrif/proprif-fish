import sqlite3
from app.config import APP_DB


def get_fish_list():
    conn = sqlite3.connect(APP_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT id, fish_name FROM fish_list")
    fish_list = cursor.fetchall()
    conn.close()

    return fish_list


def get_fish_by_id(fish_id):
    if fish_id is None:
        return None

    conn = sqlite3.connect(APP_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM fish_list WHERE id = ?", (fish_id,))
    fish = cursor.fetchone()
    conn.close()

    if fish:
        return {
            "id": fish[0],
            "name": fish[1],
            "temperature": f"{fish[4]}-{fish[5]}°C",
            "ph": f"{fish[6]}-{fish[7]}",
            "size": f"{fish[3]} cm",
            "behavior": fish[2],
        }

    return None