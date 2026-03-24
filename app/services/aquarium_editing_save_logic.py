import json


class Aquarium:
    def __init__(self, name, temperature, ph, volume):
        self.name = name
        self.temperature = temperature
        self.ph = ph
        self.volume = volume

    def update_parameters(self, name, temperature, ph, volume):
        self.name = name
        self.temperature = temperature
        self.ph = ph
        self.volume = volume

    def to_dict(self):
        return {
            "name": self.name,
            "temperature": self.temperature,
            "ph": self.ph,
            "volume": self.volume
        }

    def save_to_file(self, filename):
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(self.to_dict(), file, indent=4, ensure_ascii=False)

    @staticmethod
    def load_from_file(filename):
        try:
            with open(filename, "r", encoding="utf-8") as file:
                data = json.load(file)
                return Aquarium(
                    data["name"],
                    data["temperature"],
                    data["ph"],
                    data["volume"]
                )
        except FileNotFoundError:
            return Aquarium("Mano akvariumas", 25.0, 7.2, 120.0)


def main():
    filename = "aquarium_data.json"

    aquarium = Aquarium.load_from_file(filename)

    print("Dabartiniai akvariumo duomenys:")
    print(f"Pavadinimas: {aquarium.name}")
    print(f"Temperatūra: {aquarium.temperature} °C")
    print(f"pH: {aquarium.ph}")
    print(f"Tūris: {aquarium.volume} l")
    print()

    new_name = input("Įveskite naują akvariumo pavadinimą: ")
    new_temperature = float(input("Įveskite naują temperatūrą (°C): "))
    new_ph = float(input("Įveskite naują pH lygį: "))
    new_volume = float(input("Įveskite naują tūrį (l): "))

    aquarium.update_parameters(new_name, new_temperature, new_ph, new_volume)
    aquarium.save_to_file(filename)

    print("\nParametrai sėkmingai atnaujinti ir išsaugoti sistemoje.")


if __name__ == "__main__":
    main()