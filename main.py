from fish_data import fish_list


def show_fish_list():
    print("\nŽUVŲ SĄRAŠAS")
    print("----------------")

    for fish in fish_list:
        print(f'{fish["id"]}. {fish["name"]}')


def select_fish():
    choice = input("\nPasirinkite žuvies numerį: ")

    if not choice.isdigit():
        print("Neteisingas pasirinkimas.")
        return None

    fish_id = int(choice)

    for fish in fish_list:
        if fish["id"] == fish_id:
            return fish

    print("Tokia žuvis nerasta.")
    return None


def show_fish_info_window(fish):
    print("\n" + "=" * 35)
    print("      ŽUVIES INFORMACIJOS LANGAS")
    print("=" * 35)
    print(f'Pavadinimas: {fish["name"]}')
    print("=" * 35)

    input("\nPaspauskite Enter, kad uždaryti informacijos langą...")


def main():
    show_fish_list()

    selected_fish = select_fish()

    if selected_fish:
        show_fish_info_window(selected_fish)


if __name__ == "__main__":
    main()