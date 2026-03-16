import unittest
from multiple_aquarium_logic import create_aquarium, get_all_aquariums, add_fish, aquariums


class TestAquariumLogic(unittest.TestCase):
    
    def setUp(self):
        """Clear aquariums before each test"""
        aquariums.clear()
    
    def test_create_aquarium_success(self):
        """Test successful aquarium creation"""
        result = create_aquarium("Test Aquarium", 100)
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Akvariumas sėkmingai sukurtas.")
        self.assertEqual(len(aquariums), 1)
        self.assertEqual(aquariums[0]["name"], "Test Aquarium")
        self.assertEqual(aquariums[0]["volume"], 100)
    
    def test_create_aquarium_empty_name(self):
        """Test aquarium creation with empty name"""
        result = create_aquarium("", 100)
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Akvariumo pavadinimas privalomas.")
        self.assertEqual(len(aquariums), 0)
    
    def test_create_aquarium_whitespace_name(self):
        """Test aquarium creation with whitespace-only name"""
        result = create_aquarium("   ", 100)
        self.assertFalse(result["success"])
        self.assertEqual(len(aquariums), 0)
    
    def test_create_aquarium_invalid_volume(self):
        """Test aquarium creation with invalid volume"""
        result = create_aquarium("Test", 0)
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Akvariumo tūris turi būti didesnis už 0.")
        self.assertEqual(len(aquariums), 0)
        
        result2 = create_aquarium("Test", -50)
        self.assertFalse(result2["success"])
        self.assertEqual(len(aquariums), 0)
    
    def test_aquarium_id_generation(self):
        """Test that aquarium IDs are assigned correctly"""
        create_aquarium("First", 50)
        create_aquarium("Second", 75)
        create_aquarium("Third", 100)
        
        self.assertEqual(aquariums[0]["id"], 1)
        self.assertEqual(aquariums[1]["id"], 2)
        self.assertEqual(aquariums[2]["id"], 3)
    
    def test_get_all_aquariums(self):
        """Test retrieving all aquariums"""
        create_aquarium("Aquarium 1", 50)
        create_aquarium("Aquarium 2", 100)
        
        all_aquariums = get_all_aquariums()
        self.assertEqual(len(all_aquariums), 2)
        self.assertEqual(all_aquariums[0]["name"], "Aquarium 1")
        self.assertEqual(all_aquariums[1]["name"], "Aquarium 2")
    
    def test_add_fish_success(self):
        """Test successfully adding fish to an aquarium"""
        create_aquarium("My Aquarium", 100)
        result = add_fish(1, "Guppy", 3)
        
        self.assertEqual(result, "Žuvis pridėta")
        self.assertEqual(len(aquariums[0]["fish"]), 1)
        self.assertEqual(aquariums[0]["fish"][0]["name"], "Guppy")
        self.assertEqual(aquariums[0]["fish"][0]["size"], 3)
    
    def test_add_multiple_fish(self):
        """Test adding multiple fish to the same aquarium"""
        create_aquarium("My Aquarium", 100)
        add_fish(1, "Guppy", 3)
        add_fish(1, "Neon tetra", 2)
        add_fish(1, "Goldfish", 10)
        
        self.assertEqual(len(aquariums[0]["fish"]), 3)
    
    def test_add_fish_to_nonexistent_aquarium(self):
        """Test adding fish to an aquarium that doesn't exist"""
        result = add_fish(999, "Guppy", 3)
        self.assertEqual(result, "Akvariumas nerastas")
    
    def test_fish_structure(self):
        """Test that fish have correct structure"""
        create_aquarium("Test", 50)
        add_fish(1, "Test Fish", 5)
        
        fish = aquariums[0]["fish"][0]
        self.assertIn("name", fish)
        self.assertIn("size", fish)
        self.assertEqual(fish["name"], "Test Fish")
        self.assertEqual(fish["size"], 5)


if __name__ == "__main__":
    unittest.main()
