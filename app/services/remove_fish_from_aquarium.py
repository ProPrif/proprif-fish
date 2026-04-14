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


def remove_fish_from_aquarium(aquarium_id, fish_id, record_id=None):
    ensure_tables()
    conn = get_connection()
    cursor = conn.cursor()

    # Surandame konkretų arba pirmą įrašą kurį ištrinsime
    if record_id is not None:
        cursor.execute("""
            SELECT id FROM fish_in_aquarium
            WHERE id = ? AND aquarium_id = ? AND fish_id = ?
            LIMIT 1
        """, (record_id, aquarium_id, fish_id))
    else:
        cursor.execute("""
            SELECT id FROM fish_in_aquarium
            WHERE aquarium_id = ? AND fish_id = ?
            ORDER BY id ASC
            LIMIT 1
        """, (aquarium_id, fish_id))

    row = cursor.fetchone()

    if not row:
        conn.close()
        return {"error": "Žuvis akvariume nerasta"}

    record_id = row[0]

    # Ištriname vieną žuvį
    cursor.execute("""
        DELETE FROM fish_in_aquarium
        WHERE id = ? AND aquarium_id = ? AND fish_id = ?
    """, (record_id, aquarium_id, fish_id))

    conn.commit()
    conn.close()

    # Po ištrynimo perskaičiuojame balansą
    compatibility = recalculate_aquarium_balance(aquarium_id)

    return {
        "success": True,
        "deleted_record_id": record_id,
        "aquarium_id": aquarium_id,
        "fish_id": fish_id,
        "new_balance": compatibility
    }


def recalculate_aquarium_balance(aquarium_id):
    conn = get_connection()
    cursor = conn.cursor()

    # Gauname akvariumo tūrį
    cursor.execute("SELECT volume FROM aquarium WHERE id = ?", (aquarium_id,))
    aquarium = cursor.fetchone()

    if not aquarium:
        conn.close()
        return "UNKNOWN"

    aquarium_volume = aquarium[0]

    # Gauname visas žuvis akvariume
    cursor.execute("""
        SELECT fish_list.size,
               fish_list.aggression,
               fish_list.temp_min,
               fish_list.temp_max,
               fish_list.ph_min,
               fish_list.ph_max
        FROM fish_in_aquarium
        JOIN fish_list ON fish_in_aquarium.fish_id = fish_list.id
        WHERE fish_in_aquarium.aquarium_id = ?
    """, (aquarium_id,))

    fish = cursor.fetchall()
    conn.close()

    if not fish:
        return "EMPTY"

    total_size = 0
    aggressive_count = 0
    temp_min_list = []
    temp_max_list = []
    ph_min_list = []
    ph_max_list = []

    for f in fish:
        size, aggression, tmin, tmax, phmin, phmax = f

        total_size += size
        temp_min_list.append(tmin)
        temp_max_list.append(tmax)
        ph_min_list.append(phmin)
        ph_max_list.append(phmax)

        if aggression == "AGGRESSIVE":
            aggressive_count += 1

    # Tūrio tikrinimas
    if total_size > aquarium_volume:
        return "RED"

    # Temperatūros intervalų susikirtimas
    if max(temp_min_list) > min(temp_max_list):
        return "RED"

    # pH intervalų susikirtimas
    if max(ph_min_list) > min(ph_max_list):
        return "RED"

    # Agresyvios žuvys
    if aggressive_count > 0:
        return "YELLOW"

    return "GREEN"

if __name__ == "__main__":
    # Testavimo pavyzdys
    pass