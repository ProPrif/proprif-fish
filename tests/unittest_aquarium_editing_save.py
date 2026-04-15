import importlib
import os
import sqlite3
import tempfile
import unittest

import app.config as config
import app.database.db_setup as db_setup


TEST_DB = os.path.join(tempfile.gettempdir(), "test_aquarium_editing_save.db")


class TestAquariumEditingSave(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config.APP_DB = TEST_DB
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

        importlib.reload(db_setup)
        db_setup.create_tables()

        import app.services.aquarium_load as aquarium_load
        import app.services.aquarium_editing_save_logic as editing_logic

        importlib.reload(aquarium_load)
        importlib.reload(editing_logic)

        cls.logic = editing_logic

        conn = sqlite3.connect(TEST_DB)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO aquarium (aquarium_name, volume)
            VALUES (?, ?)
            """,
            ("Initial aquarium", 100),
        )
        cls.aquarium_id = cursor.lastrowid
        conn.commit()
        conn.close()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_validate_aquarium_data_valid(self):
        self.logic.validate_aquarium_data("My aquarium", 120)

    def test_validate_aquarium_data_empty_name(self):
        with self.assertRaisesRegex(self.logic.AquariumUpdateError, "Aquarium name is required."):
            self.logic.validate_aquarium_data("", 120)

    def test_validate_aquarium_data_invalid_volume(self):
        with self.assertRaisesRegex(
            self.logic.AquariumUpdateError,
            "Aquarium volume must be greater than 0.",
        ):
            self.logic.validate_aquarium_data("My aquarium", -5)

    def test_build_indicator_safe(self):
        result = self.logic.build_indicator("safe")
        self.assertEqual(result["status"], "safe")
        self.assertEqual(result["label"], "Safe")
        self.assertEqual(result["color"], "green")

    def test_build_indicator_warning(self):
        result = self.logic.build_indicator("warning")
        self.assertEqual(result["status"], "warning")
        self.assertEqual(result["label"], "Warning")
        self.assertEqual(result["color"], "yellow")

    def test_get_aquarium_by_id_existing(self):
        aquarium = self.logic.get_aquarium_by_id(self.aquarium_id)
        self.assertEqual(aquarium["id"], self.aquarium_id)
        self.assertEqual(aquarium["name"], "Initial aquarium")
        self.assertEqual(float(aquarium["volume"]), 100.0)

    def test_get_aquarium_by_id_not_found(self):
        with self.assertRaisesRegex(self.logic.AquariumUpdateError, "Aquarium not found."):
            self.logic.get_aquarium_by_id(999999)

    def test_update_aquarium_success(self):
        result = self.logic.update_aquarium(self.aquarium_id, "Updated aquarium", 150)

        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Aquarium details updated successfully.")
        self.assertEqual(result["aquarium"]["id"], self.aquarium_id)
        self.assertEqual(result["aquarium"]["name"], "Updated aquarium")
        self.assertEqual(float(result["aquarium"]["volume"]), 150.0)
        self.assertIn("compatibility", result)
        self.assertIn("indicator", result["compatibility"])
        self.assertIn("load", result["compatibility"])
        self.assertEqual(result["compatibility"]["indicator"]["label"], "Safe")

    def test_update_aquarium_not_found(self):
        with self.assertRaisesRegex(self.logic.AquariumUpdateError, "Aquarium not found."):
            self.logic.update_aquarium(999999, "Missing", 100)

    def test_update_aquarium_invalid_name(self):
        with self.assertRaisesRegex(self.logic.AquariumUpdateError, "Aquarium name is required."):
            self.logic.update_aquarium(self.aquarium_id, "", 100)

    def test_update_aquarium_invalid_volume(self):
        with self.assertRaisesRegex(
            self.logic.AquariumUpdateError,
            "Aquarium volume must be greater than 0.",
        ):
            self.logic.update_aquarium(self.aquarium_id, "Bad volume", 0)


if __name__ == "__main__":
    unittest.main()
