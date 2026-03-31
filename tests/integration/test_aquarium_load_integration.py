import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import app.services.aquarium_load as aquarium_load

class TestAquariumLoadIntegration(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE aquarium (
                id INTEGER PRIMARY KEY,
                aquarium_name TEXT NOT NULL,
                volume REAL NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE fish_list (
                id INTEGER PRIMARY KEY,
                fish_name TEXT NOT NULL,
                aggression TEXT NOT NULL,
                size REAL NOT NULL,
                temp_min REAL NOT NULL,
                temp_max REAL NOT NULL,
                ph_min REAL NOT NULL,
                ph_max REAL NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE fish_in_aquarium (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aquarium_id INTEGER NOT NULL,
                fish_id INTEGER NOT NULL
            )
            """
        )
        conn.commit()
        conn.close()

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except PermissionError:
                pass

    def test_calculate_load_safe(self):
        with patch("app.services.aquarium_load.APP_DB", self.db_path):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO aquarium (id, aquarium_name, volume) VALUES (?, ?, ?)",
                (1, "Test Aquarium", 100),
            )
            cursor.execute(
                "INSERT INTO fish_list (id, fish_name, aggression, size, temp_min, temp_max, ph_min, ph_max) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (1, "Goldfish", "Calm", 10, 20, 25, 6.5, 7.5),
            )
            cursor.execute(
                "INSERT INTO fish_in_aquarium (aquarium_id, fish_id) VALUES (?, ?)",
                (1, 1),
            )
            conn.commit()
            conn.close()

            result = aquarium_load.calculate_tank_load(1)

        self.assertEqual(result["status"], "safe")
        self.assertEqual(result["needed_litres"], 10)
        self.assertEqual(result["tank_volume"], 100)

    def test_calculate_load_warning(self):
        with patch("app.services.aquarium_load.APP_DB", self.db_path):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO aquarium (id, aquarium_name, volume) VALUES (?, ?, ?)",
                (1, "Test Aquarium", 50),
            )
            cursor.execute(
                "INSERT INTO fish_list (id, fish_name, aggression, size, temp_min, temp_max, ph_min, ph_max) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (1, "Goldfish", "Calm", 60, 20, 25, 6.5, 7.5),
            )
            cursor.execute(
                "INSERT INTO fish_in_aquarium (aquarium_id, fish_id) VALUES (?, ?)",
                (1, 1),
            )
            conn.commit()
            conn.close()

            result = aquarium_load.calculate_tank_load(1)

        self.assertEqual(result["status"], "warning")
        self.assertEqual(result["needed_litres"], 60)
        self.assertEqual(result["tank_volume"], 50)

if __name__ == "__main__":
    unittest.main()