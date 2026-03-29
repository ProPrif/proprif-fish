import unittest
import sqlite3
import uuid
import os
import app.config as config
import importlib
import app.database.db_setup as db_setup
from app.services.multiple_aquarium_logic import (
    create_aquarium,
    get_all_aquariums,
    add_fish_to_aquarium,
    initialize_aquarium_module
)


TEST_DB = 'test_proprif_fish_db.db'

class TestAquariumLogic(unittest.TestCase):

    def setUp(self):
        self.created_aquarium_ids = []
        self.created_fish_ids = []
        # Switch to test DB before any DB code runs
        config.APP_DB = TEST_DB
        # Remove test DB if it exists
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        # Reload db_setup and logic modules so they use the new DB path
        importlib.reload(db_setup)
        import app.services.multiple_aquarium_logic as logic
        importlib.reload(logic)
        logic.initialize_aquarium_module()
        # Print tables for debug
        conn = sqlite3.connect(config.APP_DB)
        print("TABLES:", conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
        conn.close()

    def tearDown(self):
        conn = None
        try:
            conn = sqlite3.connect(config.APP_DB)
            cursor = conn.cursor()

            for aquarium_id in self.created_aquarium_ids:
                cursor.execute(
                    "DELETE FROM fish_in_aquarium WHERE aquarium_id = ?",
                    (aquarium_id,)
                )
                cursor.execute(
                    "DELETE FROM aquarium WHERE id = ?",
                    (aquarium_id,)
                )

            for fish_id in self.created_fish_ids:
                cursor.execute(
                    "DELETE FROM fish_in_aquarium WHERE fish_id = ?",
                    (fish_id,)
                )
                cursor.execute(
                    "DELETE FROM fish_list WHERE id = ?",
                    (fish_id,)
                )

            conn.commit()
        finally:
            if conn:
                conn.close()

        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def create_test_aquarium(self, volume=100, name=None):
        if name is None:
            name = f"UNITTEST_AQUARIUM_{uuid.uuid4().hex[:8]}"

        result = create_aquarium(name, volume)

        if result["success"]:
            self.created_aquarium_ids.append(result["aquarium"]["id"])

        return result

    def insert_test_fish(self, fish_name=None, aggression="Low", size=3,
                         temp_min=22, temp_max=28, ph_min=6.5, ph_max=7.5):
        if fish_name is None:
            fish_name = f"UNITTEST_FISH_{uuid.uuid4().hex[:8]}"

        conn = None
        try:
            conn = sqlite3.connect(config.APP_DB)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO fish_list (fish_name, aggression, size, temp_min, temp_max, ph_min, ph_max)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (fish_name, aggression, size, temp_min, temp_max, ph_min, ph_max))
            fish_id = cursor.lastrowid
            conn.commit()

            self.created_fish_ids.append(fish_id)
            return fish_id
        finally:
            if conn:
                conn.close()

    def test_create_aquarium_success(self):
        result = self.create_test_aquarium(volume=100, name="UNITTEST_Test Aquarium")

        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Akvariumas sėkmingai sukurtas.")
        self.assertEqual(result["aquarium"]["name"], "UNITTEST_Test Aquarium")
        self.assertEqual(result["aquarium"]["volume"], 100)

    def test_create_aquarium_empty_name(self):
        result = create_aquarium("", 100)

        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Akvariumo pavadinimas privalomas.")

    def test_create_aquarium_whitespace_name(self):
        result = create_aquarium("   ", 100)

        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Akvariumo pavadinimas privalomas.")

    def test_create_aquarium_invalid_volume(self):
        result = create_aquarium("UNITTEST_Test", 0)
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Akvariumo tūris turi būti didesnis už 0.")

        result2 = create_aquarium("UNITTEST_Test", -50)
        self.assertFalse(result2["success"])
        self.assertEqual(result2["message"], "Akvariumo tūris turi būti didesnis už 0.")

    def test_aquarium_id_generation(self):
        result1 = self.create_test_aquarium(50)
        result2 = self.create_test_aquarium(75)
        result3 = self.create_test_aquarium(100)

        self.assertTrue(result1["success"])
        self.assertTrue(result2["success"])
        self.assertTrue(result3["success"])

        self.assertIsInstance(result1["aquarium"]["id"], int)
        self.assertIsInstance(result2["aquarium"]["id"], int)
        self.assertIsInstance(result3["aquarium"]["id"], int)

        self.assertNotEqual(result1["aquarium"]["id"], result2["aquarium"]["id"])
        self.assertNotEqual(result2["aquarium"]["id"], result3["aquarium"]["id"])

    def test_get_all_aquariums(self):
        result1 = self.create_test_aquarium(50, "UNITTEST_Aquarium_1")
        result2 = self.create_test_aquarium(100, "UNITTEST_Aquarium_2")

        all_aquariums = get_all_aquariums()

        ids = [a["id"] for a in all_aquariums]

        self.assertIn(result1["aquarium"]["id"], ids)
        self.assertIn(result2["aquarium"]["id"], ids)

        aquarium_1 = next(a for a in all_aquariums if a["id"] == result1["aquarium"]["id"])
        aquarium_2 = next(a for a in all_aquariums if a["id"] == result2["aquarium"]["id"])

        self.assertEqual(aquarium_1["name"], "UNITTEST_Aquarium_1")
        self.assertEqual(aquarium_2["name"], "UNITTEST_Aquarium_2")

    def test_add_fish_to_aquarium_success(self):
        aquarium_result = self.create_test_aquarium(100, "UNITTEST_My_Aquarium")
        aquarium_id = aquarium_result["aquarium"]["id"]

        fish_id = self.insert_test_fish(fish_name="UNITTEST_Guppy")

        result = add_fish_to_aquarium(aquarium_id, fish_id)
        self.assertEqual(result, "Žuvis pridėta į akvariumą")

        aquariums = get_all_aquariums()
        tested_aquarium = next(a for a in aquariums if a["id"] == aquarium_id)

        self.assertEqual(len(tested_aquarium["fish"]), 1)
        self.assertEqual(tested_aquarium["fish"][0]["name"], "UNITTEST_Guppy")
        self.assertEqual(tested_aquarium["fish"][0]["size"], 3)

    def test_add_multiple_fish(self):
        aquarium_result = self.create_test_aquarium(100, "UNITTEST_My_Aquarium")
        aquarium_id = aquarium_result["aquarium"]["id"]

        fish_id_1 = self.insert_test_fish("UNITTEST_Guppy", "Low", 3, 22, 28, 6.5, 7.5)
        fish_id_2 = self.insert_test_fish("UNITTEST_Neon_tetra", "Low", 2, 20, 26, 6.0, 7.0)
        fish_id_3 = self.insert_test_fish("UNITTEST_Goldfish", "Medium", 10, 18, 24, 7.0, 8.0)

        add_fish_to_aquarium(aquarium_id, fish_id_1)
        add_fish_to_aquarium(aquarium_id, fish_id_2)
        add_fish_to_aquarium(aquarium_id, fish_id_3)

        aquariums = get_all_aquariums()
        tested_aquarium = next(a for a in aquariums if a["id"] == aquarium_id)

        self.assertEqual(len(tested_aquarium["fish"]), 3)

    def test_add_fish_to_nonexistent_aquarium(self):
        fish_id = self.insert_test_fish("UNITTEST_Guppy")
        result = add_fish_to_aquarium(999999, fish_id)

        self.assertEqual(result, "Akvariumas nerastas")

    def test_add_nonexistent_fish_to_aquarium(self):
        aquarium_result = self.create_test_aquarium(100, "UNITTEST_My_Aquarium")
        aquarium_id = aquarium_result["aquarium"]["id"]

        result = add_fish_to_aquarium(aquarium_id, 999999)
        self.assertEqual(result, "Žuvis nerasta kataloge")

    def test_fish_structure(self):
        aquarium_result = self.create_test_aquarium(50, "UNITTEST_Test")
        aquarium_id = aquarium_result["aquarium"]["id"]

        fish_id = self.insert_test_fish("UNITTEST_Test_Fish", "Low", 5, 24, 27, 6.8, 7.2)
        add_fish_to_aquarium(aquarium_id, fish_id)

        aquariums = get_all_aquariums()
        tested_aquarium = next(a for a in aquariums if a["id"] == aquarium_id)
        fish = tested_aquarium["fish"][0]

        self.assertIn("name", fish)
        self.assertIn("aggression", fish)
        self.assertIn("size", fish)
        self.assertIn("temp_min", fish)
        self.assertIn("temp_max", fish)
        self.assertIn("ph_min", fish)
        self.assertIn("ph_max", fish)

        self.assertEqual(fish["name"], "UNITTEST_Test_Fish")
        self.assertEqual(fish["size"], 5)

    def test_database_persistence(self):
        aquarium_result = self.create_test_aquarium(200, "UNITTEST_Persistent_Aquarium")
        aquarium_id = aquarium_result["aquarium"]["id"]

        fish_id = self.insert_test_fish("UNITTEST_Persistent_Fish", "Low", 7, 23, 27, 6.7, 7.4)
        add_fish_to_aquarium(aquarium_id, fish_id)

        aquariums = get_all_aquariums()
        tested_aquarium = next(a for a in aquariums if a["id"] == aquarium_id)

        self.assertEqual(tested_aquarium["name"], "UNITTEST_Persistent_Aquarium")
        self.assertEqual(len(tested_aquarium["fish"]), 1)
        self.assertEqual(tested_aquarium["fish"][0]["name"], "UNITTEST_Persistent_Fish")


if __name__ == "__main__":
    unittest.main()