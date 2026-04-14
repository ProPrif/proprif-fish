import sqlite3
from enum import Enum

from app.config import APP_DB


class StatusColor(Enum):
    GREEN = "Žalia (Suderinama)"
    YELLOW = "Geltona (Atsargiai)"
    RED = "Raudona (Nesuderinama)"


class AggressionLevel(Enum):
    PEACEFUL = 1
    SEMI_AGGRESSIVE = 2
    AGGRESSIVE = 3


CODE_MESSAGES = {
    "ALL_PARAMETERS_PERFECT": "Visi pagrindiniai parametrai dera idealiai.",
    "VOLUME_LIMIT_EXCEEDED": "Akvariume nepakanka tūrio pasirinktai žuviai ir jos kiekiui.",
    "PREDATOR_ALERT": "Rastas agresyvumo konfliktas arba plėšri žuvis.",
    "SEMI_AGGRESSIVE_WARNING": "Rūšis yra pusiau agresyvi, todėl reikalingas atsargumas.",
    "TEMP_MISMATCH_CRITICAL": "Temperatūros diapazonai nesikerta kritiškai.",
    "TEMP_MISMATCH_MINOR": "Temperatūros suderinamumas ribinis, bet dar galimas.",
    "TEMP_RANGE_NARROW": "Bendras temperatūros intervalas labai siauras.",
    "PH_MISMATCH_CRITICAL": "pH diapazonai nesikerta kritiškai.",
    "PH_MISMATCH_MINOR": "pH suderinamumas ribinis, bet dar galimas.",
    "PH_RANGE_NARROW": "Bendras pH intervalas labai siauras.",
    "SOCIAL_NEED_UNMET": "Rūšiai reikia didesnio būrio.",
    "AQUARIUM_EMPTY": "Akvariumas dar tuščias, todėl vertinimas paremtas bendra žuvies informacija.",
}


class Fish:
    def __init__(
        self,
        name,
        temp_range,
        ph_range,
        min_volume,
        aggression,
        needs_school=False,
        school_min_size=5,
    ):
        self.name = name
        self.temp_min, self.temp_max = temp_range
        self.ph_min, self.ph_max = ph_range
        self.min_volume = min_volume
        self.aggression = aggression
        self.needs_school = needs_school
        self.school_min_size = school_min_size


class Aquarium:
    def __init__(self, current_temp, current_ph, available_volume):
        self.current_temp = current_temp
        self.current_ph = current_ph
        self.available_volume = available_volume


class CompatibilityChecker:
    @staticmethod
    def check_compatibility(fish: Fish, aquarium: Aquarium, quantity_to_add: int = 1) -> dict:
        alerts = []
        worst_status = StatusColor.GREEN

        required_volume = fish.min_volume * quantity_to_add
        if aquarium.available_volume < required_volume:
            worst_status = StatusColor.RED
            alerts.append("VOLUME_LIMIT_EXCEEDED")

        if fish.aggression == AggressionLevel.AGGRESSIVE:
            worst_status = StatusColor.RED
            alerts.append("PREDATOR_ALERT")
        elif fish.aggression == AggressionLevel.SEMI_AGGRESSIVE:
            if worst_status != StatusColor.RED:
                worst_status = StatusColor.YELLOW
            alerts.append("SEMI_AGGRESSIVE_WARNING")

        temp_diff = 0
        if aquarium.current_temp < fish.temp_min:
            temp_diff = fish.temp_min - aquarium.current_temp
        elif aquarium.current_temp > fish.temp_max:
            temp_diff = aquarium.current_temp - fish.temp_max

        if temp_diff > 2:
            worst_status = StatusColor.RED
            alerts.append("TEMP_MISMATCH_CRITICAL")
        elif 0 < temp_diff <= 2:
            if worst_status != StatusColor.RED:
                worst_status = StatusColor.YELLOW
            alerts.append("TEMP_MISMATCH_MINOR")

        ph_diff = 0
        if aquarium.current_ph < fish.ph_min:
            ph_diff = fish.ph_min - aquarium.current_ph
        elif aquarium.current_ph > fish.ph_max:
            ph_diff = aquarium.current_ph - fish.ph_max

        if ph_diff > 2:
            worst_status = StatusColor.RED
            alerts.append("PH_MISMATCH_CRITICAL")
        elif 0 < ph_diff <= 2:
            if worst_status != StatusColor.RED:
                worst_status = StatusColor.YELLOW
            alerts.append("PH_MISMATCH_MINOR")

        if fish.needs_school and quantity_to_add < fish.school_min_size:
            if worst_status != StatusColor.RED:
                worst_status = StatusColor.YELLOW
            alerts.append("SOCIAL_NEED_UNMET")

        if not alerts:
            alerts.append("ALL_PARAMETERS_PERFECT")

        return CompatibilityChecker._build_result(worst_status, alerts)

    @staticmethod
    def evaluate_candidate_for_aquarium(aquarium_id: int, fish_id: int, quantity_to_add: int = 1) -> dict:
        conn = sqlite3.connect(APP_DB)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, fish_name, aggression, size, temp_min, temp_max, ph_min, ph_max
                FROM fish_list
                WHERE id = ?
                """,
                (fish_id,),
            )
            fish_row = cursor.fetchone()
            if fish_row is None:
                return CompatibilityChecker._build_result(StatusColor.RED, ["PREDATOR_ALERT"])

            cursor.execute(
                "SELECT id, aquarium_name, volume FROM aquarium WHERE id = ?",
                (aquarium_id,),
            )
            aquarium_row = cursor.fetchone()
            if aquarium_row is None:
                return CompatibilityChecker._build_result(StatusColor.RED, ["VOLUME_LIMIT_EXCEEDED"])

            cursor.execute(
                """
                SELECT fl.id, fl.fish_name, fl.aggression, fl.size, fl.temp_min, fl.temp_max, fl.ph_min, fl.ph_max
                FROM fish_in_aquarium fia
                JOIN fish_list fl ON fl.id = fia.fish_id
                WHERE fia.aquarium_id = ?
                """,
                (aquarium_id,),
            )
            existing_fish = cursor.fetchall()
        finally:
            conn.close()

        candidate = fish_from_row(fish_row)
        alerts = []
        worst_status = StatusColor.GREEN

        used_volume = sum(float(row["size"]) for row in existing_fish)
        required_volume = candidate.min_volume * quantity_to_add
        if used_volume + required_volume > float(aquarium_row["volume"]):
            worst_status = StatusColor.RED
            alerts.append("VOLUME_LIMIT_EXCEEDED")

        existing_same_species = sum(1 for row in existing_fish if int(row["id"]) == fish_id)
        if candidate.needs_school and existing_same_species + quantity_to_add < candidate.school_min_size:
            if worst_status != StatusColor.RED:
                worst_status = StatusColor.YELLOW
            alerts.append("SOCIAL_NEED_UNMET")

        if not existing_fish:
            if candidate.aggression == AggressionLevel.AGGRESSIVE:
                worst_status = StatusColor.RED
                alerts.append("PREDATOR_ALERT")
            elif candidate.aggression == AggressionLevel.SEMI_AGGRESSIVE:
                if worst_status != StatusColor.RED:
                    worst_status = StatusColor.YELLOW
                alerts.append("SEMI_AGGRESSIVE_WARNING")

            alerts.append("AQUARIUM_EMPTY")
            if "ALL_PARAMETERS_PERFECT" not in alerts and len(alerts) == 1:
                alerts.insert(0, "ALL_PARAMETERS_PERFECT")
            return CompatibilityChecker._build_result(
                worst_status,
                deduplicate_codes(alerts),
                aquarium_name=aquarium_row["aquarium_name"],
                fish_name=candidate.name,
            )

        existing_temp_min = max(float(row["temp_min"]) for row in existing_fish)
        existing_temp_max = min(float(row["temp_max"]) for row in existing_fish)
        temp_overlap = min(existing_temp_max, candidate.temp_max) - max(existing_temp_min, candidate.temp_min)
        if temp_overlap < 0:
            worst_status = StatusColor.RED
            alerts.append("TEMP_MISMATCH_CRITICAL")
        elif temp_overlap < 2:
            if worst_status != StatusColor.RED:
                worst_status = StatusColor.YELLOW
            alerts.append("TEMP_RANGE_NARROW")

        existing_ph_min = max(float(row["ph_min"]) for row in existing_fish)
        existing_ph_max = min(float(row["ph_max"]) for row in existing_fish)
        ph_overlap = min(existing_ph_max, candidate.ph_max) - max(existing_ph_min, candidate.ph_min)
        if ph_overlap < 0:
            worst_status = StatusColor.RED
            alerts.append("PH_MISMATCH_CRITICAL")
        elif ph_overlap < 1:
            if worst_status != StatusColor.RED:
                worst_status = StatusColor.YELLOW
            alerts.append("PH_RANGE_NARROW")

        existing_aggressions = {map_aggression(row["aggression"]) for row in existing_fish}
        if candidate.aggression == AggressionLevel.AGGRESSIVE or AggressionLevel.AGGRESSIVE in existing_aggressions:
            worst_status = StatusColor.RED
            alerts.append("PREDATOR_ALERT")
        elif (
            candidate.aggression == AggressionLevel.SEMI_AGGRESSIVE
            or AggressionLevel.SEMI_AGGRESSIVE in existing_aggressions
        ):
            if worst_status != StatusColor.RED:
                worst_status = StatusColor.YELLOW
            alerts.append("SEMI_AGGRESSIVE_WARNING")

        if not alerts:
            alerts.append("ALL_PARAMETERS_PERFECT")

        return CompatibilityChecker._build_result(
            worst_status,
            deduplicate_codes(alerts),
            aquarium_name=aquarium_row["aquarium_name"],
            fish_name=candidate.name,
        )

    @staticmethod
    def _build_result(status: StatusColor, codes: list[str], aquarium_name: str | None = None, fish_name: str | None = None) -> dict:
        return {
            "status": status.name,
            "label": status.value,
            "color": status.value,
            "codes": codes,
            "messages": [CODE_MESSAGES.get(code, code) for code in codes],
            "aquarium_name": aquarium_name,
            "fish_name": fish_name,
        }


def deduplicate_codes(codes: list[str]) -> list[str]:
    seen = set()
    result = []
    for code in codes:
        if code in seen:
            continue
        seen.add(code)
        result.append(code)
    return result


def map_aggression(value: str | None) -> AggressionLevel:
    normalized = (value or "PEACEFUL").strip().upper()
    mapping = {
        "PEACEFUL": AggressionLevel.PEACEFUL,
        "SEMI_AGGRESSIVE": AggressionLevel.SEMI_AGGRESSIVE,
        "AGGRESSIVE": AggressionLevel.AGGRESSIVE,
    }
    return mapping.get(normalized, AggressionLevel.PEACEFUL)


def infer_schooling(name: str) -> bool:
    lowered_name = name.lower()
    schooling_keywords = (
        "tetra",
        "rasbora",
        "barb",
        "danio",
        "cory",
        "corydora",
        "minnow",
        "headstander",
    )
    return any(keyword in lowered_name for keyword in schooling_keywords)


def fish_from_row(row: sqlite3.Row) -> Fish:
    return Fish(
        name=row["fish_name"],
        temp_range=(float(row["temp_min"]), float(row["temp_max"])),
        ph_range=(float(row["ph_min"]), float(row["ph_max"])),
        min_volume=float(row["size"]),
        aggression=map_aggression(row["aggression"]),
        needs_school=infer_schooling(row["fish_name"]),
    )


if __name__ == "__main__":
    my_aquarium = Aquarium(current_temp=25, current_ph=7.0, available_volume=50)
    neon_tetra = Fish("Neoninė tetra", (22, 26), (6.0, 7.0), 2, AggressionLevel.PEACEFUL, needs_school=True)
    result_tetra = CompatibilityChecker.check_compatibility(neon_tetra, my_aquarium, quantity_to_add=1)
    print(result_tetra)
