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

    line = f"{time} | Žuvys: {', '.join(fish_names)} | Rezultatas: {result}\n"

    with open("history.txt", "a", encoding="utf-8") as file:
        file.write(line)

def delete_history_entry():
    try:
        with open("history.txt", "r", encoding="utf-8") as file:
            lines = file.readlines()

        if not lines:
            print("Istorija tuščia.")
            return

        print("\nISTORIJOS ĮRAŠAI")
        print("--------------------")

        for i, line in enumerate(lines, start=1):
            print(f"{i}. {line.strip()}")

        choice = input("\nĮveskite įrašo numerį kurį norite ištrinti: ")

        if not choice.isdigit():
            print("Neteisingas pasirinkimas.")
            return

        index = int(choice) - 1

        if index < 0 or index >= len(lines):
            print("Tokio įrašo nėra.")
            return

        del lines[index]

        with open("history.txt", "w", encoding="utf-8") as file:
            file.writelines(lines)

        print("Įrašas ištrintas.")

    except FileNotFoundError:
        print("Istorijos failas nerastas.")

def show_history():
    print("\nSUDERINAMUMO TIKRINIMŲ ISTORIJA")
    print("--------------------------------")

    try:
        with open("history.txt", "r", encoding="utf-8") as file:
            lines = file.readlines()

            if not lines:
                print("Istorija tuščia.")
                return

            for line in lines[-10:]:
                print(line.strip())

    except FileNotFoundError:
        print("Istorijos failas dar nesukurtas.")


def main():
    while True:
        print("\nMENIU")
        print("1 - Atlikti suderinamumo tikrinimą")
        print("2 - Peržiūrėti istoriją")
        print("3 - Ištrinti istorijos įrašą")
        print("0 - Išeiti")

        choice = input("Pasirinkite veiksmą: ")

        if choice == "1":
            show_fish_list()
            selected_fish = get_selected_fish()
            result = check_compatibility(selected_fish)

            if result:
                print("\nRezultatas:", result)
                save_to_history(selected_fish, result)
                print("Rezultatas išsaugotas į history.txt")

        elif choice == "2":
            show_history()
        elif choice == "3":
            delete_history_entry()

        elif choice == "0":
            print("Programa baigta.")
            break


        else:
            print("Neteisingas pasirinkimas.")


if __name__ == "__main__":
    main()