import unittest
from unittest.mock import patch

from app.services.fish_comparison_logic import (
    FishComparisonError,
    FishRecord,
    _build_aggression_result,
    _build_range_result,
    _build_size_result,
    _normalize_aggression,
    _validate_selected_ids,
    get_comparison_view_model,
)


class TestFishComparisonLogic(unittest.TestCase):
    def setUp(self):
        self.neonas = FishRecord(
            id=29,
            fish_name="Neonas",
            aggression="Rami",
            size=4.0,
            temp_min=22.0,
            temp_max=26.0,
            ph_min=6.0,
            ph_max=7.0,
        )
        self.gupija = FishRecord(
            id=30,
            fish_name="Gupija",
            aggression="Rami",
            size=5.0,
            temp_min=22.0,
            temp_max=28.0,
            ph_min=6.8,
            ph_max=7.8,
        )
        self.skaliaras = FishRecord(
            id=31,
            fish_name="Skaliaras",
            aggression="Teritorinė",
            size=15.0,
            temp_min=24.0,
            temp_max=28.0,
            ph_min=6.5,
            ph_max=7.5,
        )

    def test_validate_selected_ids_removes_duplicates(self):
        result = _validate_selected_ids([29, 29, 30])
        self.assertEqual(result, [29, 30])

    def test_validate_selected_ids_requires_at_least_two_fish(self):
        with self.assertRaises(FishComparisonError):
            _validate_selected_ids([29])

    def test_validate_selected_ids_rejects_more_than_five_fish(self):
        with self.assertRaises(FishComparisonError):
            _validate_selected_ids([1, 2, 3, 4, 5, 6])

    def test_validate_selected_ids_rejects_non_numeric_value(self):
        with self.assertRaises(FishComparisonError):
            _validate_selected_ids([29, "abc"])

    def test_normalize_aggression_understands_lithuanian_value(self):
        score, label = _normalize_aggression("Teritorinė")
        self.assertEqual(score, 2)
        self.assertEqual(label, "Pusiau agresyvi / teritorinė")

    def test_build_range_result_marks_missing_overlap_as_critical(self):
        result = _build_range_result(
            parameter_key="temperature",
            label="Temperatūros intervalas",
            values=[(22.0, 24.0), (26.0, 28.0)],
            unit=" °C",
            narrow_overlap_threshold=2.0,
        )

        self.assertEqual(result["severity"], "critical")
        self.assertTrue(result["significant_difference"])
        self.assertIsNone(result["overlap"])

    def test_build_size_result_marks_large_size_gap_as_critical(self):
        result = _build_size_result([self.neonas, self.skaliaras])

        self.assertEqual(result["severity"], "critical")
        self.assertTrue(result["significant_difference"])
        self.assertEqual(result["ratio"], 3.75)

    def test_build_aggression_result_marks_peaceful_and_aggressive_mix(self):
        aggressive = FishRecord(
            id=99,
            fish_name="Cichlida",
            aggression="Agresyvi",
            size=12.0,
            temp_min=24.0,
            temp_max=28.0,
            ph_min=6.5,
            ph_max=7.5,
        )

        result = _build_aggression_result([self.neonas, aggressive])

        self.assertEqual(result["severity"], "critical")
        self.assertTrue(result["significant_difference"])
        self.assertIn("ramios", result["message"].lower())

    @patch("app.services.fish_comparison_logic._fetch_fish_by_ids")
    @patch("app.services.fish_comparison_logic.ensure_tables")
    def test_get_comparison_view_model_success(self, mocked_ensure_tables, mocked_fetch):
        mocked_fetch.return_value = [self.neonas, self.gupija, self.skaliaras]

        result = get_comparison_view_model([29, 30, 31])

        mocked_ensure_tables.assert_called_once()
        mocked_fetch.assert_called_once_with([29, 30, 31])
        self.assertEqual(result["window_title"], "Žuvų palyginimas")
        self.assertFalse(result["reload_required"])
        self.assertEqual(result["comparison"]["selected_count"], 3)
        self.assertEqual(result["comparison"]["overall_status"], "critical")
        self.assertEqual(len(result["comparison"]["selected_fish"]), 3)
        self.assertEqual(result["comparison"]["actions"]["available_fish_ids"], [29, 30, 31])

    @patch("app.services.fish_comparison_logic._fetch_fish_by_ids")
    @patch("app.services.fish_comparison_logic.ensure_tables")
    def test_get_comparison_view_model_raises_when_fish_missing(self, mocked_ensure_tables, mocked_fetch):
        mocked_fetch.return_value = [self.neonas, self.gupija]

        with self.assertRaises(FishComparisonError) as context:
            get_comparison_view_model([29, 30, 31])

        mocked_ensure_tables.assert_called_once()
        mocked_fetch.assert_called_once_with([29, 30, 31])
        self.assertIn("31", str(context.exception))


if __name__ == "__main__":
    unittest.main()
