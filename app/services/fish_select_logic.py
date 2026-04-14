import sqlite3
from app.config import APP_DB


def show_fish_list():
    print("\nŽUVŲ SĄRAŠAS")
    print("----------------")

    conn = sqlite3.connect(APP_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT id, fish_name FROM fish_list")
    fish_list = cursor.fetchall()
    conn.close()

    for fish in fish_list:
        print(f'{fish[0]}. {fish[1]}')


def select_fish():
    choice = input("\nPasirinkite žuvies numerį: ")

    if not choice.isdigit():
        print("Neteisingas pasirinkimas.")
        return None

    fish_id = int(choice)

    conn = sqlite3.connect(APP_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM fish_list WHERE id = ?", (fish_id,))
    fish = cursor.fetchone()
    conn.close()

    if fish:
        return {
            "id": fish[0],
            "name": fish[1],
            "temperature": f"{fish[4]}-{fish[5]}°C",
            "ph": f"{fish[6]}-{fish[7]}",
            "size": f"{fish[3]} cm",
            "behavior": fish[2]
        }

    print("Tokia žuvis nerasta.")
    return None

def show_fish_info_window(fish):
    print("\n" + "=" * 40)
    print("        ŽUVIES INFORMACIJOS LANGAS")
    print("=" * 40)

    print(f"Pavadinimas: {fish['name']}")
    print(f"Rekomenduojama temperatūra: {fish['temperature']}")
    print(f"Rekomenduojamas pH intervalas: {fish['ph']}")
    print(f"Maksimalus žuvies dydis: {fish['size']}")
    print(f"Elgsena: {fish['behavior']}")

    print("=" * 40)

    input("\nPaspauskite Enter, kad uždaryti informacijos langą...")


def main():
    show_fish_list()

    selected_fish = select_fish()

    if selected_fish:
        show_fish_info_window(selected_fish)


if __name__ == "__main__":
    main()