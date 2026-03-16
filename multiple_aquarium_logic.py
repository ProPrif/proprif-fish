import sqlite3
import os

# Database setup
DB_FILE = 'aquarium.db'

def get_db_connection():
    """Get database connection and create tables if they don't exist"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    create_tables(conn)
    return conn

def create_tables(conn):
    """Create database tables if they don't exist"""
    conn.execute('''
        CREATE TABLE IF NOT EXISTS aquariums (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            volume REAL NOT NULL
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS fish (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aquarium_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            size REAL NOT NULL,
            FOREIGN KEY (aquarium_id) REFERENCES aquariums (id) ON DELETE CASCADE
        )
    ''')

    conn.commit()

def create_aquarium(name, volume):
    if not name or name.strip() == "":
        return {"success": False, "message": "Akvariumo pavadinimas privalomas."}

    if volume <= 0:
        return {"success": False, "message": "Akvariumo tūris turi būti didesnis už 0."}

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('INSERT INTO aquariums (name, volume) VALUES (?, ?)', (name, volume))
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
        if 'conn' in locals():
            conn.close()

def get_all_aquariums():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get all aquariums
        cursor.execute('SELECT * FROM aquariums')
        aquariums_data = cursor.fetchall()

        aquariums = []
        for aquarium_row in aquariums_data:
            # Get fish for this aquarium
            cursor.execute('SELECT name, size FROM fish WHERE aquarium_id = ?', (aquarium_row['id'],))
            fish_data = cursor.fetchall()

            fish_list = [{"name": fish['name'], "size": fish['size']} for fish in fish_data]

            aquarium = {
                "id": aquarium_row['id'],
                "name": aquarium_row['name'],
                "volume": aquarium_row['volume'],
                "fish": fish_list
            }
            aquariums.append(aquarium)

        return aquariums
    except sqlite3.Error as e:
        print(f"Duomenų bazės klaida: {str(e)}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()

def add_fish(aquarium_id, fish_name, size):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if aquarium exists
        cursor.execute('SELECT id FROM aquariums WHERE id = ?', (aquarium_id,))
        if not cursor.fetchone():
            return "Akvariumas nerastas"

        # Add fish
        cursor.execute('INSERT INTO fish (aquarium_id, name, size) VALUES (?, ?, ?)',
                      (aquarium_id, fish_name, size))
        conn.commit()

        return "Žuvis pridėta"
    except sqlite3.Error as e:
        return f"Duomenų bazės klaida: {str(e)}"
    finally:
        if 'conn' in locals():
            conn.close()


