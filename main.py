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


def main():
    show_fish_list()

    selected_fish = select_fish()

    if selected_fish:
        print(f"\nPasirinkta žuvis: {selected_fish['name']}")


if __name__ == "__main__":
    main()