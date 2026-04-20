from functools import lru_cache

from app.services.aquarium_indicator_logic import AggressionLevel
from app.services.fish_logic import get_all_fish

STATUS_SELF = 0
STATUS_GREEN = 1
STATUS_YELLOW = 2
STATUS_RED = 3


def map_db_to_fish(db_fish: dict) -> tuple[str, int, float, float, float, float]:
    aggression_map = {
        "PEACEFUL": AggressionLevel.PEACEFUL.value,
        "SEMI_AGGRESSIVE": AggressionLevel.SEMI_AGGRESSIVE.value,
        "AGGRESSIVE": AggressionLevel.AGGRESSIVE.value,
    }

    return (
        db_fish["fish_name"],
        aggression_map.get(db_fish["aggression"], AggressionLevel.PEACEFUL.value),
        float(db_fish["temp_min"]),
        float(db_fish["temp_max"]),
        float(db_fish["ph_min"]),
        float(db_fish["ph_max"]),
    )


def check_fish_pair_code(fish1: tuple[str, int, float, float, float, float], fish2: tuple[str, int, float, float, float, float]) -> int:
    aggression_1 = fish1[1]
    aggression_2 = fish2[1]

    if aggression_1 == AggressionLevel.AGGRESSIVE.value or aggression_2 == AggressionLevel.AGGRESSIVE.value:
        return STATUS_RED

    status = STATUS_YELLOW if (
        aggression_1 == AggressionLevel.SEMI_AGGRESSIVE.value
        or aggression_2 == AggressionLevel.SEMI_AGGRESSIVE.value
    ) else STATUS_GREEN

    temp_min = fish1[2] if fish1[2] > fish2[2] else fish2[2]
    temp_max = fish1[3] if fish1[3] < fish2[3] else fish2[3]
    if temp_min > temp_max:
        return STATUS_RED
    if (temp_max - temp_min) < 2:
        status = STATUS_YELLOW

    ph_min = fish1[4] if fish1[4] > fish2[4] else fish2[4]
    ph_max = fish1[5] if fish1[5] < fish2[5] else fish2[5]
    if ph_min > ph_max:
        return STATUS_RED
    if (ph_max - ph_min) < 1:
        status = STATUS_YELLOW

    return status


@lru_cache(maxsize=1)
def build_compatibility_matrix() -> dict:
    fish_objects = [map_db_to_fish(row) for row in get_all_fish()]
    count = len(fish_objects)
    matrix = [bytearray(count) for _ in range(count)]

    for index in range(count):
        matrix[index][index] = STATUS_SELF

    for left_index in range(count):
        left_fish = fish_objects[left_index]
        left_row = matrix[left_index]
        for right_index in range(left_index + 1, count):
            status = check_fish_pair_code(left_fish, fish_objects[right_index])
            left_row[right_index] = status
            matrix[right_index][left_index] = status

    return {
        "fish": [fish[0] for fish in fish_objects],
        "matrix": matrix,
    }
