import sqlite3
import unittest

from app.config import APP_DB
from app.services.aquarium_editing_save_logic import (
    AquariumUpdateError,
    build_indicator,
    get_aquarium_by_id,
    update_aquarium,
    validate_aquarium_data,
)


class TestAquariumEditingSave(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        conn = sqlite3.connect(APP_DB)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO aquarium (aquarium_name, volume)
            VALUES (?, ?)
            """,
            ("Testinis akvariumas", 100),
        )
        cls.aquarium_id = cursor.lastrowid

        conn.commit()
        conn.close()

    @classmethod
    def tearDownClass(cls):
        conn = sqlite3.connect(APP_DB)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM aquarium WHERE id = ?", (cls.aquarium_id,))
        conn.commit()
        conn.close()

    def test_validate_aquarium_data_valid(self):
        validate_aquarium_data("Mano akvariumas", 120)

    def test_validate_aquarium_data_empty_name(self):
        with self.assertRaises(AquariumUpdateError):
            validate_aquarium_data("", 120)

    def test_validate_aquarium_data_invalid_volume(self):
        with self.assertRaises(AquariumUpdateError):
            validate_aquarium_data("Mano akvariumas", -5)

    def test_build_indicator_safe(self):
        result = build_indicator("safe")
        self.assertEqual(result["status"], "safe")
        self.assertEqual(result["label"], "Suderinama")
        self.assertEqual(result["color"], "green")

    def test_build_indicator_warning(self):
        result = build_indicator("warning")
        self.assertEqual(result["status"], "warning")
        self.assertEqual(result["label"], "Atsargiai")
        self.assertEqual(result["color"], "yellow")

    def test_get_aquarium_by_id_existing(self):
        aquarium = get_aquarium_by_id(self.aquarium_id)
        self.assertEqual(aquarium["id"], self.aquarium_id)
        self.assertIn("name", aquarium)
        self.assertIn("volume", aquarium)

    def test_get_aquarium_by_id_not_found(self):
        with self.assertRaises(AquariumUpdateError):
            get_aquarium_by_id(999999)

    def test_update_aquarium_success(self):
        result = update_aquarium(self.aquarium_id, "Test akvariumas", 150)

        self.assertTrue(result["success"])
        self.assertEqual(result["aquarium"]["id"], self.aquarium_id)
        self.assertEqual(result["aquarium"]["name"], "Test akvariumas")
        self.assertEqual(float(result["aquarium"]["volume"]), 150.0)
        self.assertIn("compatibility", result)
        self.assertIn("indicator", result["compatibility"])
        self.assertIn("load", result["compatibility"])

    def test_update_aquarium_not_found(self):
        with self.assertRaises(AquariumUpdateError):
            update_aquarium(999999, "Nerastas", 100)

    def test_update_aquarium_invalid_name(self):
        with self.assertRaises(AquariumUpdateError):
            update_aquarium(self.aquarium_id, "", 100)

    def test_update_aquarium_invalid_volume(self):
        with self.assertRaises(AquariumUpdateError):
            update_aquarium(self.aquarium_id, "Blogas tūris", 0)


if __name__ == "__main__":
    unittest.main()