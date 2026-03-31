import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys

sys.path.append(str(Path(__file__).resolve().parents[2]))

import app.services.remove_fish_from_aquarium as remove_service


class TestFishRemoveIntegration(unittest.TestCase):
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

    def test_integration_remove_updates_balance(self):
        with patch("app.services.remove_fish_from_aquarium.APP_DB", self.db_path):
            with patch("app.services.remove_fish_from_aquarium.ensure_tables", lambda: None):
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO aquarium (id, aquarium_name, volume)
                    VALUES (1, 'Test Aquarium', 10.0)
                    """
                )
                cursor.execute(
                    """
                    INSERT INTO fish_list
                    (id, fish_name, aggression, size, temp_min, temp_max, ph_min, ph_max)
                    VALUES (1, 'Neon', 'CALM', 15.0, 20, 25, 6, 8)
                    """
                )
                cursor.execute(
                    "INSERT INTO fish_in_aquarium (aquarium_id, fish_id) VALUES (1, 1)"
                )
                conn.commit()
                conn.close()

                response = remove_service.remove_fish_from_aquarium(1, 1)

        self.assertEqual(response["new_balance"], "EMPTY")
        self.assertTrue(response["success"])

    def test_integration_error_handling_integrity(self):
        with patch("app.services.remove_fish_from_aquarium.APP_DB", self.db_path):
            with patch("app.services.remove_fish_from_aquarium.ensure_tables", lambda: None):
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO aquarium (id, aquarium_name, volume)
                    VALUES (1, 'Test Aquarium', 10.0)
                    """
                )
                cursor.execute(
                    """
                    INSERT INTO fish_list
                    (id, fish_name, aggression, size, temp_min, temp_max, ph_min, ph_max)
                    VALUES (1, 'Neon', 'CALM', 15.0, 20, 25, 6, 8)
                    """
                )
                cursor.execute(
                    "INSERT INTO fish_in_aquarium (aquarium_id, fish_id) VALUES (1, 1)"
                )
                conn.commit()
                conn.close()

                response = remove_service.remove_fish_from_aquarium(1, 999)
                current_balance = remove_service.recalculate_aquarium_balance(1)

        self.assertIn("error", response)
        self.assertEqual(current_balance, "RED")


if __name__ == "__main__":
    unittest.main()
