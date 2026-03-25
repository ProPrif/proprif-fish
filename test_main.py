import unittest
from unittest.mock import patch, mock_open
import main


class TestFishCompatibility(unittest.TestCase):

    def test_check_compatibility_with_less_than_two_fish(self):
        selected_fish = [{"id": 1, "name": "Neonas"}]

        with patch("builtins.print") as mocked_print:
            result = main.check_compatibility(selected_fish)

        self.assertIsNone(result)
        mocked_print.assert_called_with("Reikia pasirinkti bent 2 žuvis.")

    def test_check_compatibility_with_two_fish(self):
        selected_fish = [
            {"id": 1, "name": "Neonas"},
            {"id": 2, "name": "Gupija"}
        ]

        result = main.check_compatibility(selected_fish)

        self.assertEqual(result, "Suderinamos")

    @patch("builtins.open", new_callable=mock_open)
    def test_save_to_history(self, mocked_file):
        selected_fish = [
            {"id": 1, "name": "Neonas"},
            {"id": 2, "name": "Gupija"}
        ]
        result = "Suderinamos"

        main.save_to_history(selected_fish, result)

        mocked_file.assert_called_once_with("history.txt", "a", encoding="utf-8")
        handle = mocked_file()

        written_text = "".join(call.args[0] for call in handle.write.call_args_list)

        self.assertIn("Žuvys: Neonas, Gupija", written_text)
        self.assertIn("Rezultatas: Suderinamos", written_text)

    @patch("builtins.open", new_callable=mock_open, read_data="")
    def test_show_history_empty(self, mocked_file):
        with patch("builtins.print") as mocked_print:
            main.show_history()

        mocked_print.assert_any_call("Istorija tuščia.")

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="2026-01-01 10:00:00 | Žuvys: Neonas | Rezultatas: Suderinamos\n"
                  "2026-01-02 11:00:00 | Žuvys: Gupija | Rezultatas: Suderinamos\n"
    )
    def test_show_history_with_entries(self, mocked_file):
        with patch("builtins.print") as mocked_print:
            main.show_history()

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
            main.delete_history_entry()

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
    def test_show_history_file_not_found(self, mocked_open):
        with patch("builtins.print") as mocked_print:
            main.show_history()

        mocked_print.assert_any_call("Istorijos failas dar nesukurtas.")

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_delete_history_entry_file_not_found(self, mocked_open):
        with patch("builtins.print") as mocked_print:
            main.delete_history_entry()

        mocked_print.assert_any_call("Istorijos failas nerastas.")


if __name__ == "__main__":
    unittest.main()