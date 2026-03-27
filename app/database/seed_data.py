import sqlite3
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import APP_DB


def add_fish_to_db(fish_name, aggression, size, temp_min, temp_max, ph_min, ph_max):
    """Add a single fish to the fish_list table"""
    conn = sqlite3.connect(APP_DB)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO fish_list (fish_name, aggression, size, temp_min, temp_max, ph_min, ph_max)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (fish_name, aggression, size, temp_min, temp_max, ph_min, ph_max))
    conn.commit()
    conn.close()
    print(f"Added {fish_name} to the database")


def seed_fish_data():
    """Populate fish_list table with sample data"""
    fish_data = [
        ("Neonas", "Rami", 4, 22, 26, 6.0, 7.0),
        ("Gupija", "Rami", 5, 22, 28, 6.8, 7.8),
        ("Skaliaras", "Teritorinė", 15, 24, 28, 6.5, 7.5),
    ]
    
    conn = sqlite3.connect(APP_DB)
    cursor = conn.cursor()
    for fish_name, aggression, size, temp_min, temp_max, ph_min, ph_max in fish_data:
        cursor.execute("""
            INSERT INTO fish_list (fish_name, aggression, size, temp_min, temp_max, ph_min, ph_max)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (fish_name, aggression, size, temp_min, temp_max, ph_min, ph_max))
    conn.commit()
    conn.close()
    print("Fish data seeded successfully")


if __name__ == "__main__":
    seed_fish_data()
