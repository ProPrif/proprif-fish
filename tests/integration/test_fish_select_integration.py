import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import app.services.fish_select_logic as fish_select_logic


class TestFishSelectIntegration(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
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
            """
        )
        cursor.executemany(
            """
            INSERT INTO fish_list (fish_name, aggression, size, temp_min, temp_max, ph_min, ph_max)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("Neonas", "Rami", 4, 22, 26, 6.0, 7.0),
                ("Gupija", "Rami", 5, 22, 28, 6.8, 7.8),
                ("Skaliaras", "Teritorinė", 15, 24, 28, 6.5, 7.5),
            ],
        )
        conn.commit()
        conn.close()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_show_fish_list_and_select(self):
        with patch("app.services.fish_select_logic.APP_DB", self.db_path):
            with patch("builtins.print") as mocked_print:
                fish_select_logic.show_fish_list()

            mocked_print.assert_any_call("\nŽUVŲ SĄRAŠAS")
            mocked_print.assert_any_call("----------------")
            mocked_print.assert_any_call("1. Neonas")
            mocked_print.assert_any_call("2. Gupija")
            mocked_print.assert_any_call("3. Skaliaras")

            with patch("builtins.input", return_value="2"):
                result = fish_select_logic.select_fish()

        self.assertIsNotNone(result)
        self.assertEqual(result["id"], 2)
        self.assertEqual(result["name"], "Gupija")
        self.assertEqual(result["temperature"], "22.0-28.0°C")
        self.assertEqual(result["ph"], "6.8-7.8")
        self.assertEqual(result["size"], "5.0 cm")
        self.assertEqual(result["behavior"], "Rami")


if __name__ == "__main__":
    unittest.main()
