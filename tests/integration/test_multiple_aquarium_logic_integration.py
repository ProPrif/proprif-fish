import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import app.services.multiple_aquarium_logic as multiple_logic

class TestMultipleAquariumLogicIntegration(unittest.TestCase):
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
            os.remove(self.db_path)

    def test_create_aquarium_success(self):
        with patch("app.services.multiple_aquarium_logic.APP_DB", self.db_path):
            response = multiple_logic.create_aquarium("Test Aquarium", 50)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT aquarium_name, volume FROM aquarium WHERE aquarium_name = ?",
                ("Test Aquarium",)
            )
            row = cursor.fetchone()
            conn.close()

        self.assertTrue(response["success"])
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "Test Aquarium")
        self.assertEqual(row[1], 50)

    def test_get_all_aquariums(self):
        with patch("app.services.multiple_aquarium_logic.APP_DB", self.db_path):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO aquarium (aquarium_name, volume) VALUES (?, ?)",
                ("Aquarium 1", 30),
            )
            cursor.execute(
                "INSERT INTO aquarium (aquarium_name, volume) VALUES (?, ?)",
                ("Aquarium 2", 60),
            )
            conn.commit()
            conn.close()

            aquariums = multiple_logic.get_all_aquariums()

        self.assertEqual(len(aquariums), 2)
        self.assertEqual(aquariums[0]["name"], "Aquarium 1")
        self.assertEqual(aquariums[1]["volume"], 60)

if __name__ == "__main__":
    unittest.main()