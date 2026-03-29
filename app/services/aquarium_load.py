import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import sqlite3
from app.config import APP_DB


def get_db_connection():
    conn = sqlite3.connect(APP_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def calculate_tank_load(aquarium_id):
    """
    Calculates the current load of the tank and returns status.
    - Sums the total length (cm) of all fish in the tank (1cm = 1L needed)
    - Compares to the tank's volume (L)
    - Returns dict: { 'needed_litres': int, 'tank_volume': int, 'status': 'safe'|'warning' }
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Get tank volume
        cursor.execute("SELECT volume FROM aquarium WHERE id = ?", (aquarium_id,))
        row = cursor.fetchone()
        if not row:
            return {'error': 'Aquarium not found'}
        tank_volume = row['volume']

        # Get all fish in this aquarium (with their sizes)
        cursor.execute("""
            SELECT fl.size, COUNT(*) as count
            FROM fish_in_aquarium fia
            JOIN fish_list fl ON fia.fish_id = fl.id
            WHERE fia.aquarium_id = ?
            GROUP BY fl.id
        """, (aquarium_id,))
        fish_data = cursor.fetchall()

        # Calculate total needed litres
        needed_litres = sum(fish['size'] * fish['count'] for fish in fish_data)

        status = 'safe' if needed_litres <= tank_volume else 'warning'
        return {
            'needed_litres': needed_litres,
            'tank_volume': tank_volume,
            'status': status
        }
    finally:
        conn.close()


# if __name__ == "__main__":
    # Example: Check tank load for aquarium with ID 1
    # aquarium_id = 1
    # result = calculate_tank_load(aquarium_id)
    # print(f"Aquarium {aquarium_id} load status:")
    # print(result)
