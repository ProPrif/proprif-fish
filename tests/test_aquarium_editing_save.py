import os
import unittest
from app.services.aquarium_editing_save_logic import Aquarium


class TestAquarium(unittest.TestCase):

    def setUp(self):
        self.test_file = "test_aquarium.json"
        self.aquarium = Aquarium("Test Akvariumas", 24.0, 7.1, 100)

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_update_parameters(self):
        self.aquarium.update_parameters("Naujas", 26.0, 7.5, 150)

        self.assertEqual(self.aquarium.name, "Naujas")
        self.assertEqual(self.aquarium.temperature, 26.0)
        self.assertEqual(self.aquarium.ph, 7.5)
        self.assertEqual(self.aquarium.volume, 150)

    def test_save_to_file(self):
        self.aquarium.save_to_file(self.test_file)

        self.assertTrue(os.path.exists(self.test_file))

    def test_load_from_file(self):
        self.aquarium.save_to_file(self.test_file)

        loaded = Aquarium.load_from_file(self.test_file)

        self.assertEqual(loaded.name, "Test Akvariumas")
        self.assertEqual(loaded.temperature, 24.0)
        self.assertEqual(loaded.ph, 7.1)
        self.assertEqual(loaded.volume, 100)


if __name__ == "__main__":
    unittest.main()