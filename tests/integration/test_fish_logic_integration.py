import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import app.services.fish_logic as fish_logic


class TestFishLogicIntegration(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        self.db_patches = [
            patch("app.services.fish_logic.APP_DB", self.db_path),
            patch("app.database.db_setup.APP_DB", self.db_path),
        ]

        for db_patch in self.db_patches:
            db_patch.start()

        fish_logic.initialize_fish_module()

    def tearDown(self):
        for db_patch in reversed(self.db_patches):
            db_patch.stop()

        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_fish_crud_flow_uses_real_database(self):
        created_fish = fish_logic.add_fish(
            "Guppy",
            "Calm",
            4.0,
            22.0,
            26.0,
            6.5,
            7.5,
        )

        self.assertIsNotNone(created_fish)
        self.assertEqual(created_fish["fish_name"], "Guppy")

        fish_from_id = fish_logic.get_fish_by_id(created_fish["id"])
        self.assertEqual(fish_from_id, created_fish)

        all_fish = fish_logic.get_all_fish()
        self.assertEqual(len(all_fish), 1)
        self.assertEqual(all_fish[0], created_fish)

        fish_parameters = fish_logic.get_fish_parameters()
        self.assertEqual(
            fish_parameters,
            [
                {
                    "fish_name": "Guppy",
                    "aggression": "Calm",
                    "size": 4.0,
                    "temp_min": 22.0,
                    "temp_max": 26.0,
                    "ph_min": 6.5,
                    "ph_max": 7.5,
                }
            ],
        )

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM fish_list")
        self.assertEqual(cursor.fetchone()[0], 1)
        conn.close()

        fish_logic.clear_fish_table()
        self.assertEqual(fish_logic.get_all_fish(), [])


if __name__ == "__main__":
    unittest.main()
