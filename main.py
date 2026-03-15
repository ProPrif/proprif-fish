from fish_data import fish_list
from datetime import datetime


def show_fish_list():
    print("\nGALIMOS ŽUVYS")
    print("----------------")

    for fish in fish_list:
        print(f'{fish["id"]}. {fish["name"]}')


def get_selected_fish():
    ids = input("\nĮveskite žuvų numerius (pvz: 1,2): ")

    ids = ids.split(",")
    selected = []

    for id in ids:
        id = int(id.strip())

        for fish in fish_list:
            if fish["id"] == id:
                selected.append(fish)

    return selected


def check_compatibility(selected_fish):
    if len(selected_fish) < 2:
        print("Reikia pasirinkti bent 2 žuvis.")
        return None

    result = "Suderinamos"
    return result


def save_to_history(selected_fish, result):
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fish_names = [fish["name"] for fish in selected_fish]

    new_line = f"{time} | Žuvys: {', '.join(fish_names)} | Rezultatas: {result}\n"

    try:
        with open("history.txt", "r", encoding="utf-8") as file:
            lines = file.readlines()
    except FileNotFoundError:
        lines = []

    lines.append(new_line)

    if len(lines) > 10:
        lines = lines[-10:]

    with open("history.txt", "w", encoding="utf-8") as file:
        file.writelines(lines)


def main():
    show_fish_list()

    selected_fish = get_selected_fish()
    result = check_compatibility(selected_fish)

    if result:
        print("\nRezultatas:", result)
        save_to_history(selected_fish, result)
        print("Rezultatas išsaugotas į history.txt")


if __name__ == "__main__":
    main()