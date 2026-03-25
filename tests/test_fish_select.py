import unittest
from unittest.mock import patch
import app.services.fish_select_logic as fish_select_logic


class TestFishProgram(unittest.TestCase):

    def test_show_fish_list(self):
        with patch("builtins.print") as mocked_print:
            fish_select_logic.show_fish_list()

        mocked_print.assert_any_call("\nŽUVŲ SĄRAŠAS")
        mocked_print.assert_any_call("----------------")
        mocked_print.assert_any_call("1. Neonas")
        mocked_print.assert_any_call("2. Gupija")
        mocked_print.assert_any_call("3. Skaliaras")

    @patch("builtins.input", return_value="1")
    def test_select_fish_valid(self, mocked_input):
        result = fish_select_logic.select_fish()

        self.assertIsNotNone(result)
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["name"], "Neonas")

    @patch("builtins.input", return_value="abc")
    def test_select_fish_invalid_input(self, mocked_input):
        with patch("builtins.print") as mocked_print:
            result = fish_select_logic.select_fish()

        self.assertIsNone(result)
        mocked_print.assert_called_with("Neteisingas pasirinkimas.")

    @patch("builtins.input", return_value="999")
    def test_select_fish_not_found(self, mocked_input):
        with patch("builtins.print") as mocked_print:
            result = fish_select_logic.select_fish()

        self.assertIsNone(result)
        mocked_print.assert_called_with("Tokia žuvis nerasta.")

    @patch("builtins.input", return_value="")
    def test_show_fish_info_window(self, mocked_input):
        fish = {
            "id": 1,
            "name": "Neonas",
            "temperature": "22-26°C",
            "ph": "6.0-7.0",
            "size": "4 cm",
            "behavior": "Rami",
            "description": "Maža, spalvinga ir taiki akvariumo žuvis."
        }

        with patch("builtins.print") as mocked_print:
            fish_select_logic.show_fish_info_window(fish)

        mocked_print.assert_any_call("        ŽUVIES INFORMACIJOS LANGAS")
        mocked_print.assert_any_call("Pavadinimas: Neonas")
        mocked_print.assert_any_call("Rekomenduojama temperatūra: 22-26°C")
        mocked_print.assert_any_call("Rekomenduojamas pH intervalas: 6.0-7.0")
        mocked_print.assert_any_call("Maksimalus žuvies dydis: 4 cm")
        mocked_print.assert_any_call("Elgsena: Rami")
        mocked_print.assert_any_call("\nAprašymas:")
        mocked_print.assert_any_call("Maža, spalvinga ir taiki akvariumo žuvis.")


if __name__ == "__main__":
    unittest.main()