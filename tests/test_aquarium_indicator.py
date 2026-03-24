import unittest
from aquarium_indicator_logic import Fish, Aquarium, CompatibilityChecker, StatusColor, AggressionLevel

class TestCompatibilityChecker(unittest.TestCase):

    def setUp(self):
        # Sukuriame bazinį akvariumą, kurį naudosime daugelyje testų
        # Temp: 25, pH: 7.0, Tūris: 50
        self.base_aquarium = Aquarium(current_temp=25, current_ph=7.0, available_volume=50)

    def test_all_parameters_perfect(self):
        # Viskas atitinka idealiai
        perfect_fish = Fish("Taiki", (24, 26), (6.5, 7.5), 10, AggressionLevel.PEACEFUL, False)
        result = CompatibilityChecker.check_compatibility(perfect_fish, self.base_aquarium, 1)
        
        self.assertEqual(result["color"], StatusColor.GREEN.value)
        self.assertIn("ALL_PARAMETERS_PERFECT", result["codes"])

    def test_volume_limit_exceeded(self):
        # Tūrio trūkumas (10 vnt. * 10L = 100L > 50L) -> RAUDONA
        big_fish = Fish("Didelė", (24, 26), (6.5, 7.5), 10, AggressionLevel.PEACEFUL, False)
        result = CompatibilityChecker.check_compatibility(big_fish, self.base_aquarium, 10)
        
        self.assertEqual(result["color"], StatusColor.RED.value)
        self.assertIn("VOLUME_LIMIT_EXCEEDED", result["codes"])

    def test_predator_alert(self):
        # Plėšrūnas -> RAUDONA
        predator = Fish("Plėšrūnas", (24, 26), (6.5, 7.5), 10, AggressionLevel.AGGRESSIVE, False)
        result = CompatibilityChecker.check_compatibility(predator, self.base_aquarium, 1)
        
        self.assertEqual(result["color"], StatusColor.RED.value)
        self.assertIn("PREDATOR_ALERT", result["codes"])

    def test_semi_aggressive_warning(self):
        # Pusiau agresyvi -> GELTONA
        semi = Fish("Gaidukas", (24, 26), (6.5, 7.5), 10, AggressionLevel.SEMI_AGGRESSIVE, False)
        result = CompatibilityChecker.check_compatibility(semi, self.base_aquarium, 1)
        
        self.assertEqual(result["color"], StatusColor.YELLOW.value)
        self.assertIn("SEMI_AGGRESSIVE_WARNING", result["codes"])

    def test_temp_mismatch_minor_too_cold(self):
        # Akvariumo temp (25) yra per žema žuviai (26-28), skirtumas 1 -> GELTONA
        warm_fish = Fish("Šilumą mėgstanti", (26, 28), (6.5, 7.5), 10, AggressionLevel.PEACEFUL, False)
        result = CompatibilityChecker.check_compatibility(warm_fish, self.base_aquarium, 1)
        
        self.assertEqual(result["color"], StatusColor.YELLOW.value)
        self.assertIn("TEMP_MISMATCH_MINOR", result["codes"])

    def test_temp_mismatch_critical_too_hot(self):
        # Akvariumo temp (25) yra per aukšta žuviai (20-22), skirtumas 3 -> RAUDONA
        cold_fish = Fish("Šaltavandenė", (20, 22), (6.5, 7.5), 10, AggressionLevel.PEACEFUL, False)
        result = CompatibilityChecker.check_compatibility(cold_fish, self.base_aquarium, 1)
        
        self.assertEqual(result["color"], StatusColor.RED.value)
        self.assertIn("TEMP_MISMATCH_CRITICAL", result["codes"])

    def test_ph_mismatch_minor_too_acidic(self):
        # Akvariumo pH (7.0) per žemas žuviai (8.0-8.5), skirtumas 1.0 -> GELTONA
        high_ph_fish = Fish("Šarminė", (24, 26), (8.0, 8.5), 10, AggressionLevel.PEACEFUL, False)
        result = CompatibilityChecker.check_compatibility(high_ph_fish, self.base_aquarium, 1)
        
        self.assertEqual(result["color"], StatusColor.YELLOW.value)
        self.assertIn("PH_MISMATCH_MINOR", result["codes"])

    def test_ph_mismatch_critical_too_alkaline(self):
        # Akvariumo pH (7.0) per aukštas žuviai (4.0-4.5), skirtumas 2.5 -> RAUDONA
        low_ph_fish = Fish("Rūgštinė", (24, 26), (4.0, 4.5), 10, AggressionLevel.PEACEFUL, False)
        result = CompatibilityChecker.check_compatibility(low_ph_fish, self.base_aquarium, 1)
        
        self.assertEqual(result["color"], StatusColor.RED.value)
        self.assertIn("PH_MISMATCH_CRITICAL", result["codes"])

    def test_social_need_unmet(self):
        # Reikia būrio, bet perkama tik 1 -> GELTONA
        schooling_fish = Fish("Tetra", (24, 26), (6.5, 7.5), 5, AggressionLevel.PEACEFUL, needs_school=True)
        result = CompatibilityChecker.check_compatibility(schooling_fish, self.base_aquarium, 1)
        
        self.assertEqual(result["color"], StatusColor.YELLOW.value)
        self.assertIn("SOCIAL_NEED_UNMET", result["codes"])

    def test_worst_status_precedence(self):
        # Tikriname, ar RAUDONA "permuša" GELTONĄ.
        # Žuvis: pusiau agresyvi (GELTONA), bet akvariumo tūris per mažas (RAUDONA).
        big_semi_fish = Fish("Didelis Cichlidas", (24, 26), (6.5, 7.5), 100, AggressionLevel.SEMI_AGGRESSIVE, False)
        result = CompatibilityChecker.check_compatibility(big_semi_fish, self.base_aquarium, 1)
        
        self.assertEqual(result["color"], StatusColor.RED.value)
        self.assertIn("VOLUME_LIMIT_EXCEEDED", result["codes"])
        self.assertIn("SEMI_AGGRESSIVE_WARNING", result["codes"])


if __name__ == "__main__":
    unittest.main()