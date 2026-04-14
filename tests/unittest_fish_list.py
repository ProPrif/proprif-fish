import unittest
from unittest.mock import patch, mock_open, ANY
import app.services.fish_list as fish_list


class TestFishCompatibility(unittest.TestCase):

    def test_check_compatibility_with_less_than_two_fish(self):
        selected_fish = [{"id": 1, "name": "Neonas"}]

        with patch("builtins.print") as mocked_print:
            result = fish_list.check_compatibility(selected_fish)

        self.assertIsNone(result)
        mocked_print.assert_called_with("Reikia pasirinkti bent 2 žuvis.")

    def test_check_compatibility_with_two_fish(self):
        selected_fish = [
            {"id": 1, "name": "Neonas"},
            {"id": 2, "name": "Gupija"}
        ]

        result = fish_list.check_compatibility(selected_fish)

        self.assertEqual(result, "Suderinamos")

    @patch("app.services.fish_list.sqlite3.connect")
    def test_save_to_history(self, mocked_connect):
        selected_fish = [
            {"id": 1, "name": "Neonas"},
            {"id": 2, "name": "Gupija"}
        ]
        result = "Suderinamos"

        fish_list.save_to_history(selected_fish, result)

        mocked_connect.assert_called_once()
        conn = mocked_connect.return_value
        cursor = conn.cursor.return_value

        cursor.execute.assert_called_once_with(
            """
        INSERT INTO compatibility_history (timestamp, fish_names, result)
        VALUES (?, ?, ?)
    """,
            (ANY, "Neonas, Gupija", "Suderinamos")
        )
        conn.commit.assert_called_once()
        conn.close.assert_called_once()

    @patch("app.services.fish_list.sqlite3.connect")
    def test_show_history_empty(self, mocked_connect):
        conn = mocked_connect.return_value
        cursor = conn.cursor.return_value
        cursor.fetchall.return_value = []

        with patch("builtins.print") as mocked_print:
            fish_list.show_history()

        cursor.execute.assert_called_once_with(
            "SELECT timestamp, fish_names, result FROM compatibility_history ORDER BY timestamp DESC LIMIT 10"
        )
        conn.close.assert_called_once()
        mocked_print.assert_any_call("Istorija tuščia.")

    @patch("app.services.fish_list.sqlite3.connect")
    def test_show_history_with_entries(self, mocked_connect):
        conn = mocked_connect.return_value
        cursor = conn.cursor.return_value
        cursor.fetchall.return_value = [
            ("2026-01-01 10:00:00", "Neonas", "Suderinamos"),
            ("2026-01-02 11:00:00", "Gupija", "Suderinamos")
        ]

        with patch("builtins.print") as mocked_print:
            fish_list.show_history()

        cursor.execute.assert_called_once_with(
            "SELECT timestamp, fish_names, result FROM compatibility_history ORDER BY timestamp DESC LIMIT 10"
        )
        conn.close.assert_called_once()
        mocked_print.assert_any_call("2026-01-01 10:00:00 | Žuvys: Neonas | Rezultatas: Suderinamos")
        mocked_print.assert_any_call("2026-01-02 11:00:00 | Žuvys: Gupija | Rezultatas: Suderinamos")

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="2026-01-01 10:00:00 | Žuvys: Neonas | Rezultatas: Suderinamos\n"
                  "2026-01-02 11:00:00 | Žuvys: Gupija | Rezultatas: Suderinamos\n"
    )
    @patch("builtins.input", return_value="1")
    def test_delete_history_entry(self, mocked_input, mocked_file):
        with patch("builtins.print"):
            fish_list.delete_history_entry()

        handle = mocked_file()

        written_text = "".join(handle.writelines.call_args[0][0])

        self.assertNotIn(
            "2026-01-01 10:00:00 | Žuvys: Neonas | Rezultatas: Suderinamos\n",
            written_text
        )
        self.assertIn(
            "2026-01-02 11:00:00 | Žuvys: Gupija | Rezultatas: Suderinamos\n",
            written_text
        )

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_delete_history_entry_file_not_found(self, mocked_open):
        with patch("builtins.print") as mocked_print:
            fish_list.delete_history_entry()

        mocked_print.assert_any_call("Istorijos failas nerastas.")


if __name__ == "__main__":
    unittest.main()