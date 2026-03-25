import app.services.fish_logic as fish_logic


def test_add_fish_returns_record():
    fish_logic.clear_fish_table()

    result = fish_logic.add_fish("Guppy", 24.5, "low", 4.0)

    assert result is not None
    assert result[1] == "Guppy"
    assert result[2] == 24.5
    assert result[3] == "low"
    assert result[4] == 4.0


def test_fish_is_saved_in_database():
    fish_logic.clear_fish_table()

    fish_logic.add_fish("Neon", 25.0, "low", 3.5)

    fish_logic.cursor.execute("SELECT * FROM fish WHERE name = ?", ("Neon",))
    result = fish_logic.cursor.fetchone()

    assert result is not None
    assert result[1] == "Neon"


def test_multiple_fish_can_be_added():
    fish_logic.clear_fish_table()

    fish_logic.add_fish("Fish1", 22.0, "low", 2.0)
    fish_logic.add_fish("Fish2", 26.0, "medium", 5.0)

    fish_logic.cursor.execute("SELECT COUNT(*) FROM fish")
    count = fish_logic.cursor.fetchone()[0]

    assert count == 2


def test_id_is_created_automatically():
    fish_logic.clear_fish_table()

    result = fish_logic.add_fish("Molly", 26.0, "medium", 5.5)

    assert isinstance(result[0], int)
    assert result[0] > 0


def run_all_tests():
    test_add_fish_returns_record()
    print("test_add_fish_returns_record passed")

    test_fish_is_saved_in_database()
    print("test_fish_is_saved_in_database passed")

    test_multiple_fish_can_be_added()
    print("test_multiple_fish_can_be_added passed")

    test_id_is_created_automatically()
    print("test_id_is_created_automatically passed")

    print("Visi testai sėkmingai įvykdyti.")


if __name__ == "__main__":
    run_all_tests()
    fish_logic.conn.close()