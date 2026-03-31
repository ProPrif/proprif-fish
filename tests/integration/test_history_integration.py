import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import app.services.fish_list as fish_list


class TestHistoryIntegration(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS compatibility_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                fish_names TEXT NOT NULL,
                result TEXT NOT NULL
            )
            """
        )
        conn.commit()
        conn.close()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_save_and_show_history(self):
        selected_fish = [
            {"id": 1, "name": "Neonas"},
            {"id": 2, "name": "Gupija"},
        ]
        result = "Suderinamos"

        with patch("app.services.fish_list.APP_DB", self.db_path):
            fish_list.save_to_history(selected_fish, result)

            with patch("builtins.print") as mocked_print:
                fish_list.show_history()

        printed_lines = [call.args[0] for call in mocked_print.call_args_list]
        self.assertTrue(
            any("Žuvys: Neonas, Gupija | Rezultatas: Suderinamos" in line for line in printed_lines)
        )


if __name__ == "__main__":
    unittest.main()
