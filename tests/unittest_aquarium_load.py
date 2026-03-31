import unittest
import sqlite3
import os
from app.services import aquarium_load
from app.database import db_setup
from app.config import APP_DB

class TestAquariumLoad(unittest.TestCase):
    TEST_DB = 'test_proprif_fish_db.db'

    @classmethod
    def setUpClass(cls):
        # Patch the DB path for testing
        cls._orig_db = APP_DB
        import app.config
        app.config.APP_DB = cls.TEST_DB
        # Remove test DB if it exists before creating tables
        if os.path.exists(cls.TEST_DB):
            os.remove(cls.TEST_DB)
        # Print debug info
        print("APP_DB:", app.config.APP_DB)
        # Directly create tables in the test DB using sqlite3
        import sqlite3
        conn = sqlite3.connect(cls.TEST_DB)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS aquarium (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aquarium_name TEXT NOT NULL,
                volume REAL NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fish_list (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fish_name TEXT NOT NULL,
                aggression TEXT NOT NULL,
                size REAL NOT NULL,
                temp_min REAL NOT NULL,
                temp_max REAL NOT NULL,
                ph_min REAL NOT NULL,
                ph_max REAL NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fish_in_aquarium (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aquarium_id INTEGER NOT NULL,
                fish_id INTEGER NOT NULL,
                FOREIGN KEY (aquarium_id) REFERENCES aquarium(id) ON DELETE CASCADE,
                FOREIGN KEY (fish_id) REFERENCES fish_list(id) ON DELETE CASCADE
            )
        """)
        conn.commit()
        print("TABLES:", cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
        conn.close()
        # Reload aquarium_load so it uses the correct DB
        import importlib
        import app.services.aquarium_load as aquarium_load_mod
        importlib.reload(aquarium_load_mod)
        globals()['aquarium_load'] = aquarium_load_mod

    @classmethod
    def tearDownClass(cls):
        import app.config
        app.config.APP_DB = cls._orig_db
        # Ensure all connections are closed before deleting
        import gc
        gc.collect()
        if os.path.exists(cls.TEST_DB):
            try:
                os.remove(cls.TEST_DB)
            except PermissionError:
                pass  # If still locked, ignore for now

    def setUp(self):
        # Ensure tables exist before cleaning
        import app.database.db_setup
        app.database.db_setup.create_tables()
        conn = sqlite3.connect(self.TEST_DB)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM fish_in_aquarium')
        cursor.execute('DELETE FROM fish_list')
        cursor.execute('DELETE FROM aquarium')
        conn.commit()
        conn.close()

    def test_aquarium_not_found(self):
        result = aquarium_load.calculate_tank_load(1)
        self.assertIn('error', result)
        self.assertEqual(result['error'], 'Aquarium not found')

    def test_empty_aquarium(self):
        # Create aquarium with 50L
        conn = sqlite3.connect(self.TEST_DB)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO aquarium (aquarium_name, volume) VALUES (?, ?)", ("TestTank", 50))
        aquarium_id = cursor.lastrowid
        conn.commit()
        conn.close()
        result = aquarium_load.calculate_tank_load(aquarium_id)
        self.assertEqual(result['needed_litres'], 0)
        self.assertEqual(result['tank_volume'], 50)
        self.assertEqual(result['status'], 'safe')

    def test_safe_load(self):
        # Create aquarium and fish
        conn = sqlite3.connect(self.TEST_DB)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO aquarium (aquarium_name, volume) VALUES (?, ?)", ("TestTank", 10))
        aquarium_id = cursor.lastrowid
        cursor.execute("INSERT INTO fish_list (fish_name, aggression, size, temp_min, temp_max, ph_min, ph_max) VALUES (?, ?, ?, ?, ?, ?, ?)", ("SmallFish", "Low", 2, 20, 25, 6.5, 7.5))
        fish_id = cursor.lastrowid
        # Add 3 fish (total 6cm)
        for _ in range(3):
            cursor.execute("INSERT INTO fish_in_aquarium (aquarium_id, fish_id) VALUES (?, ?)", (aquarium_id, fish_id))
        conn.commit()
        conn.close()
        result = aquarium_load.calculate_tank_load(aquarium_id)
        self.assertEqual(result['needed_litres'], 6)
        self.assertEqual(result['tank_volume'], 10)
        self.assertEqual(result['status'], 'safe')

    def test_warning_load(self):
        # Create aquarium and fish
        conn = sqlite3.connect(self.TEST_DB)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO aquarium (aquarium_name, volume) VALUES (?, ?)", ("TestTank", 5))
        aquarium_id = cursor.lastrowid
        cursor.execute("INSERT INTO fish_list (fish_name, aggression, size, temp_min, temp_max, ph_min, ph_max) VALUES (?, ?, ?, ?, ?, ?, ?)", ("BigFish", "High", 3, 20, 25, 6.5, 7.5))
        fish_id = cursor.lastrowid
        # Add 2 fish (total 6cm)
        for _ in range(2):
            cursor.execute("INSERT INTO fish_in_aquarium (aquarium_id, fish_id) VALUES (?, ?)", (aquarium_id, fish_id))
        conn.commit()
        conn.close()
        result = aquarium_load.calculate_tank_load(aquarium_id)
        self.assertEqual(result['needed_litres'], 6)
        self.assertEqual(result['tank_volume'], 5)
        self.assertEqual(result['status'], 'warning')

if __name__ == "__main__":
    unittest.main()
