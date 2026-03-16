aquariums = []


def create_aquarium(name, volume):
    if not name or name.strip() == "":
        return {"success": False, "message": "Akvariumo pavadinimas privalomas."}

    if volume <= 0:
        return {"success": False, "message": "Akvariumo tūris turi būti didesnis už 0."}

    aquarium = {
        "id": len(aquariums) + 1,
        "name": name,
        "volume": volume,
        "fish": []
    }

    aquariums.append(aquarium)

    return {
        "success": True,
        "message": "Akvariumas sėkmingai sukurtas.",
        "aquarium": aquarium
    }

def get_all_aquariums():
    return aquariums

def add_fish(aquarium_id, fish_name, size):
    for aquarium in aquariums:
        if aquarium["id"] == aquarium_id:
            fish = {
                "name": fish_name,
                "size": size
            }
            aquarium["fish"].append(fish)
            return "Žuvis pridėta"

    return "Akvariumas nerastas"

