from enum import Enum


class StatusColor(Enum):
    GREEN = "Žalia (Suderinama)"
    YELLOW = "Geltona (Atsargiai)"
    RED = "Raudona (Nesuderinama)"


class AggressionLevel(Enum):
    PEACEFUL = 1
    SEMI_AGGRESSIVE = 2
    AGGRESSIVE = 3


# --- Pagrindinės klasės ---
class Fish:
    def __init__(self, name, temp_range, ph_range, min_volume, aggression, needs_school=False):
        self.name = name
        self.temp_min, self.temp_max = temp_range
        self.ph_min, self.ph_max = ph_range
        self.min_volume = min_volume
        self.aggression = aggression
        self.needs_school = needs_school


class Aquarium:
    def __init__(self, current_temp, current_ph, available_volume):
        self.current_temp = current_temp
        self.current_ph = current_ph
        self.available_volume = available_volume


# --- Suderinamumo Algoritmas ---
class CompatibilityChecker:
    @staticmethod
    def check_compatibility(fish: Fish, aquarium: Aquarium, quantity_to_add: int = 1) -> dict:
        alerts = []
        worst_status = StatusColor.GREEN

        # 1. Tūrio patikrinimas (Kritinis -> Raudona)
        required_volume = fish.min_volume * quantity_to_add
        if aquarium.available_volume < required_volume:
            worst_status = StatusColor.RED
            alerts.append("VOLUME_LIMIT_EXCEEDED")

        # 2. Agresyvumo patikrinimas (Plėšrūnas -> Raudona, Pusiau agresyvi -> Geltona)
        if fish.aggression == AggressionLevel.AGGRESSIVE:
            worst_status = StatusColor.RED
            alerts.append("PREDATOR_ALERT")
        elif fish.aggression == AggressionLevel.SEMI_AGGRESSIVE:
            if worst_status != StatusColor.RED:
                worst_status = StatusColor.YELLOW
            alerts.append("SEMI_AGGRESSIVE_WARNING")

        # 3. Temperatūros patikrinimas (1-2 paklaida -> Geltona, >2 -> Raudona)
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

        # 4. pH patikrinimas (1-2 paklaida -> Geltona, >2 -> Raudona)
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

        # 5. Socialinio poreikio patikrinimas (Būrio trūkumas -> Geltona)
        # Tarkime, minimalus būrys yra 5 žuvytės
        if fish.needs_school and quantity_to_add < 5:
            if worst_status != StatusColor.RED:
                worst_status = StatusColor.YELLOW
            alerts.append("SOCIAL_NEED_UNMET")

        # Jei nėra jokių problemų
        if not alerts:
            alerts.append("ALL_PARAMETERS_PERFECT")

        return {
            "color": worst_status.value,
            "codes": alerts
        }


# --- Naudojimo pavyzdys (Testavimas) ---
if __name__ == "__main__":
    # Turimas akvariumas: 25 laipsniai, pH 7.0, likęs laisvas tūris 50 litrų
    my_aquarium = Aquarium(current_temp=25, current_ph=7.0, available_volume=50)

    # Sukuriame žuvis testavimui
    neon_tetra = Fish("Neoninė tetra", temp_range=(22, 26), ph_range=(6.0, 7.0), min_volume=2,
                      aggression=AggressionLevel.PEACEFUL, needs_school=True)
    cichlid = Fish("Cichlidas plėšrūnas", temp_range=(24, 28), ph_range=(7.5, 8.5), min_volume=100,
                   aggression=AggressionLevel.AGGRESSIVE)
    betta = Fish("Gaidukas", temp_range=(24, 28), ph_range=(6.5, 7.5), min_volume=10,
                 aggression=AggressionLevel.SEMI_AGGRESSIVE)

    print("--- Pasirenkama žuvies kortelė: Neoninė tetra (perkama 1 vnt.) ---")
    # Trūksta socialinio poreikio (perkama tik 1), bus GELTONA
    result_tetra = CompatibilityChecker.check_compatibility(neon_tetra, my_aquarium, quantity_to_add=1)
    print(f"Spalva: {result_tetra['color']}")
    print(f"Kodai: {', '.join(result_tetra['codes'])}\n")

    print("--- Pasirenkama žuvies kortelė: Neoninė tetra (perkamas būrys - 6 vnt.) ---")
    # Viskas atitinka, bus ŽALIA
    result_tetra_school = CompatibilityChecker.check_compatibility(neon_tetra, my_aquarium, quantity_to_add=6)
    print(f"Spalva: {result_tetra_school['color']}")
    print(f"Kodai: {', '.join(result_tetra_school['codes'])}\n")

    print("--- Pasirenkama žuvies kortelė: Cichlidas plėšrūnas ---")
    # Tūris per mažas, plėšrūnas, pH netinka. Bus RAUDONA
    result_cichlid = CompatibilityChecker.check_compatibility(cichlid, my_aquarium, quantity_to_add=1)
    print(f"Spalva: {result_cichlid['color']}")
    print(f"Kodai: {', '.join(result_cichlid['codes'])}\n")

    print("--- Pasirenkama žuvies kortelė: Gaidukas ---")
    # Tinka pagal tūrį, temp, bet yra pusiau agresyvus. Bus GELTONA
    result_betta = CompatibilityChecker.check_compatibility(betta, my_aquarium, quantity_to_add=1)
    print(f"Spalva: {result_betta['color']}")
    print(f"Kodai: {', '.join(result_betta['codes'])}\n")