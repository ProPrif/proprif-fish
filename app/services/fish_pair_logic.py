from app.services.fish_logic import get_all_fish
from app.services.aquarium_indicator_logic import (
    Fish,
    AggressionLevel
)


def map_db_to_fish(db_fish):
    aggression_map = {
        "PEACEFUL": AggressionLevel.PEACEFUL,
        "SEMI_AGGRESSIVE": AggressionLevel.SEMI_AGGRESSIVE,
        "AGGRESSIVE": AggressionLevel.AGGRESSIVE
    }

    return Fish(
        name=db_fish["fish_name"],
        temp_range=(db_fish["temp_min"], db_fish["temp_max"]),
        ph_range=(db_fish["ph_min"], db_fish["ph_max"]),
        min_volume=0,  # не нужен для fish-fish
        aggression=aggression_map.get(db_fish["aggression"], AggressionLevel.PEACEFUL),
        needs_school=False
    )


def check_fish_pair(fish1: Fish, fish2: Fish):
    worst_status = "GREEN"

    if fish1.aggression == AggressionLevel.AGGRESSIVE or fish2.aggression == AggressionLevel.AGGRESSIVE:
        return "RED"

    if (
        fish1.aggression == AggressionLevel.SEMI_AGGRESSIVE
        or fish2.aggression == AggressionLevel.SEMI_AGGRESSIVE
    ):
        worst_status = "YELLOW"

    temp_min = max(fish1.temp_min, fish2.temp_min)
    temp_max = min(fish1.temp_max, fish2.temp_max)

    if temp_min > temp_max:
        return "RED"

    if (temp_max - temp_min) < 2:
        if worst_status != "RED":
            worst_status = "YELLOW"

    ph_min = max(fish1.ph_min, fish2.ph_min)
    ph_max = min(fish1.ph_max, fish2.ph_max)

    if ph_min > ph_max:
        return "RED"

    if (ph_max - ph_min) < 1:
        if worst_status != "RED":
            worst_status = "YELLOW"

    return worst_status


def build_compatibility_matrix():
    db_fish_list = get_all_fish()

    fish_objects = [map_db_to_fish(f) for f in db_fish_list]

    n = len(fish_objects)

    matrix = [["-" for _ in range(n)] for _ in range(n)]

    for i in range(n):
        for j in range(i, n):

            if i == j:
                matrix[i][j] = "SELF"
                continue

            status = check_fish_pair(fish_objects[i], fish_objects[j])

            matrix[i][j] = status
            matrix[j][i] = status

    return {
        "fish": [f.name for f in fish_objects],
        "matrix": matrix
    }