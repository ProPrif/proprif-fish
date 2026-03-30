import unittest
import os
import sqlite3
import app.services.fish_logic as fish_logic

TEST_DB = r".\..\data\test_fish.db"


def create_test_fish_table():
    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()

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

    conn.commit()
    conn.close()


class TestFishLogic(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        fish_logic.APP_DB = TEST_DB
        create_test_fish_table()

    def setUp(self):
        fish_logic.clear_fish_table()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_add_fish(self):
        result = fish_logic.add_fish("Guppy", "low", 4.0, 22.0, 26.0, 6.5, 7.5)

        self.assertIsNotNone(result)
        self.assertEqual(result["fish_name"], "Guppy")

    def test_get_all_fish(self):
        fish_logic.add_fish("Neon", "low", 3.5, 23.0, 27.0, 6.0, 7.0)

        result = fish_logic.get_all_fish()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["fish_name"], "Neon")

    def test_multiple_fish(self):
        fish_logic.add_fish("Fish1", "low", 2.0, 20.0, 24.0, 6.0, 7.0)
        fish_logic.add_fish("Fish2", "medium", 5.0, 24.0, 28.0, 7.0, 8.0)

        result = fish_logic.get_all_fish()

        self.assertEqual(len(result), 2)

    def test_get_fish_by_id(self):
        fish = fish_logic.add_fish("Platy", "low", 4.5, 22.0, 26.0, 7.0, 8.0)

        result = fish_logic.get_fish_by_id(fish["id"])

        self.assertIsNotNone(result)
        self.assertEqual(result["fish_name"], "Platy")

    def test_get_fish_by_id_not_found(self):
        result = fish_logic.get_fish_by_id(999)

        self.assertIsNone(result)

    def test_get_fish_parameters(self):
        fish_logic.add_fish("Discus", "medium", 15.0, 27.0, 30.0, 6.0, 7.0)

        result = fish_logic.get_fish_parameters()

        self.assertEqual(len(result), 1)
        self.assertNotIn("id", result[0])

    def test_clear_table(self):
        fish_logic.add_fish("Test", "low", 2.0, 20.0, 24.0, 6.0, 7.0)

        fish_logic.clear_fish_table()
        result = fish_logic.get_all_fish()

        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()