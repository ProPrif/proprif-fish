import sqlite3
from app.config import APP_DB
from datetime import datetime


def show_fish_list():
    print("\nGALIMOS ŽUVYS")
    print("----------------")

    conn = sqlite3.connect(APP_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT id, fish_name FROM fish_list")
    fish_list = cursor.fetchall()
    conn.close()

    for fish in fish_list:
        print(f'{fish[0]}. {fish[1]}')


def get_selected_fish():
    ids = input("\nĮveskite žuvų numerius (pvz: 1,2): ")

    ids = ids.split(",")
    selected = []

    conn = sqlite3.connect(APP_DB)
    cursor = conn.cursor()

    for id in ids:
        id = int(id.strip())
        cursor.execute("SELECT * FROM fish_list WHERE id = ?", (id,))
        fish = cursor.fetchone()

        if fish:
            selected.append({
                "id": fish[0],
                "name": fish[1],
                "temperature": f"{fish[4]}-{fish[5]}°C",
                "ph": f"{fish[6]}-{fish[7]}",
                "size": f"{fish[3]} cm",
                "behavior": fish[2]
            })

    conn.close()
    
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

    conn = sqlite3.connect(APP_DB)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO compatibility_history (timestamp, fish_names, result)
        VALUES (?, ?, ?)
    """, (time, ', '.join(fish_names), result))
    conn.commit()
    conn.close()

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

    conn = sqlite3.connect(APP_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, fish_names, result FROM compatibility_history ORDER BY timestamp DESC LIMIT 10")
    history_entries = cursor.fetchall()
    conn.close()

    if not history_entries:
        print("Istorija tuščia.")
        return

    for entry in history_entries:
        print(f"{entry[0]} | Žuvys: {entry[1]} | Rezultatas: {entry[2]}")


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
                print("Rezultatas išsaugotas į duomenų bazę")

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