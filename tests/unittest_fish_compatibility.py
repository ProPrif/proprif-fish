import unittest

from app.services.fish_pair_logic import (
    map_db_to_fish,
    check_fish_pair,
    build_compatibility_matrix
)


class TestFishCompatibility(unittest.TestCase):

    def setUp(self):
        self.fish_data = [
            {
                "id": 1,
                "fish_name": "Neon",
                "aggression": "PEACEFUL",
                "size": 2,
                "temp_min": 22,
                "temp_max": 26,
                "ph_min": 6.0,
                "ph_max": 7.0
            },
            {
                "id": 2,
                "fish_name": "Guppy",
                "aggression": "PEACEFUL",
                "size": 3,
                "temp_min": 23,
                "temp_max": 27,
                "ph_min": 6.5,
                "ph_max": 7.5
            },
            {
                "id": 3,
                "fish_name": "Cichlid",
                "aggression": "AGGRESSIVE",
                "size": 10,
                "temp_min": 24,
                "temp_max": 28,
                "ph_min": 7.5,
                "ph_max": 8.5
            }
        ]

    # --- map_db_to_fish ---
    def test_map_db_to_fish(self):
        fish = map_db_to_fish(self.fish_data[0])

        self.assertEqual(fish.name, "Neon")
        self.assertEqual(fish.temp_min, 22)
        self.assertEqual(fish.temp_max, 26)

    # --- YELLOW (из-за pH пересечения < 1) ---
    def test_check_fish_pair_yellow(self):
        f1 = map_db_to_fish(self.fish_data[0])
        f2 = map_db_to_fish(self.fish_data[1])

        result = check_fish_pair(f1, f2)

        self.assertEqual(result, "YELLOW")

    # --- RED (агрессия) ---
    def test_check_fish_pair_aggressive(self):
        f1 = map_db_to_fish(self.fish_data[0])
        f2 = map_db_to_fish(self.fish_data[2])

        result = check_fish_pair(f1, f2)

        self.assertEqual(result, "RED")

    # --- RED (температура не пересекается) ---
    def test_check_fish_pair_temp_mismatch(self):
        fish1 = {
            "fish_name": "ColdFish",
            "aggression": "PEACEFUL",
            "size": 2,
            "temp_min": 10,
            "temp_max": 15,
            "ph_min": 6,
            "ph_max": 7
        }

        fish2 = {
            "fish_name": "HotFish",
            "aggression": "PEACEFUL",
            "size": 2,
            "temp_min": 25,
            "temp_max": 30,
            "ph_min": 6,
            "ph_max": 7
        }

        f1 = map_db_to_fish(fish1)
        f2 = map_db_to_fish(fish2)

        result = check_fish_pair(f1, f2)

        self.assertEqual(result, "RED")

    # --- матрица ---
    def test_build_compatibility_matrix(self):
        import app.services.fish_pair_logic as fish_compatibility_service

        # мок БД
        original_func = fish_compatibility_service.get_all_fish
        fish_compatibility_service.get_all_fish = lambda: self.fish_data

        try:
            result = build_compatibility_matrix()

            matrix = result["matrix"]

            # размер
            self.assertEqual(len(matrix), 3)

            # диагональ
            self.assertEqual(matrix[0][0], "SELF")

            # симметрия
            self.assertEqual(matrix[0][1], matrix[1][0])

            # агрессивная рыба даёт RED
            self.assertEqual(matrix[0][2], "RED")

        finally:
            fish_compatibility_service.get_all_fish = original_func


if __name__ == "__main__":
    unittest.main()