import sqlite3

import pytest

from app.services import search_and_add_fish as service_module
from app.services.search_and_add_fish import (
    add_fish_to_aquarium,
    get_aquarium_fish,
    search_fish,
)


def _init_schema(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE fish_list (
            id INTEGER PRIMARY KEY,
            fish_name TEXT NOT NULL,
            aggression TEXT NOT NULL,
            size INTEGER NOT NULL
        );

        CREATE TABLE fish_in_aquarium (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aquarium_id INTEGER NOT NULL,
            fish_id INTEGER NOT NULL
        );
        """
    )
    conn.commit()
    conn.close()


def _exec(db_path: str, query: str, params=()) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    conn.close()


def _fetchall(db_path: str, query: str, params=()):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def _insert_fish(
    db_path: str,
    fish_id: int,
    fish_name: str,
    aggression: str = "CALM",
    size: int = 5,
) -> None:
    _exec(
        db_path,
        """
        INSERT INTO fish_list (id, fish_name, aggression, size)
        VALUES (?, ?, ?, ?)
        """,
        (fish_id, fish_name, aggression, size),
    )


def _insert_fish_in_aquarium(
    db_path: str, aquarium_id: int, fish_id: int, quantity: int = 1
) -> None:
    for _ in range(quantity):
        _exec(
            db_path,
            "INSERT INTO fish_in_aquarium (aquarium_id, fish_id) VALUES (?, ?)",
            (aquarium_id, fish_id),
        )


@pytest.fixture
def db_env(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test_search_add.sqlite3")
    _init_schema(db_path)
    monkeypatch.setattr(service_module, "APP_DB", db_path)
    monkeypatch.setattr(service_module, "ensure_tables", lambda: None)
    return db_path


def test_search_fish_returns_partial_name_matches(db_env):
    _insert_fish(db_env, fish_id=1, fish_name="Goldfish", aggression="CALM", size=4)
    _insert_fish(db_env, fish_id=2, fish_name="Angel Fish", aggression="SEMI", size=6)
    _insert_fish(db_env, fish_id=3, fish_name="Catfish", aggression="CALM", size=7)

    result = search_fish("fish")

    assert result == [
        (1, "Goldfish", "CALM", 4),
        (2, "Angel Fish", "SEMI", 6),
        (3, "Catfish", "CALM", 7),
    ]


def test_search_fish_returns_empty_list_when_no_match(db_env):
    _insert_fish(db_env, fish_id=1, fish_name="Goldfish")

    result = search_fish("shark")

    assert result == []


def test_add_fish_to_aquarium_returns_error_for_non_positive_quantity(db_env):
    _insert_fish(db_env, fish_id=1, fish_name="Goldfish")

    result = add_fish_to_aquarium(aquarium_id=1, fish_id=1, quantity=0)

    assert result == {"error": "Kiekis turi būti > 0"}
    assert _fetchall(db_env, "SELECT aquarium_id, fish_id FROM fish_in_aquarium") == []


def test_add_fish_to_aquarium_returns_error_when_fish_does_not_exist(db_env):
    result = add_fish_to_aquarium(aquarium_id=1, fish_id=999, quantity=2)

    assert result == {"error": "Žuvis nerasta"}
    assert _fetchall(db_env, "SELECT aquarium_id, fish_id FROM fish_in_aquarium") == []


def test_add_fish_to_aquarium_inserts_requested_quantity(db_env):
    _insert_fish(db_env, fish_id=1, fish_name="Goldfish")

    result = add_fish_to_aquarium(aquarium_id=5, fish_id=1, quantity=3)

    assert result == {"success": True}
    assert _fetchall(
        db_env,
        "SELECT aquarium_id, fish_id FROM fish_in_aquarium ORDER BY id",
    ) == [(5, 1), (5, 1), (5, 1)]


def test_get_aquarium_fish_returns_grouped_quantities_for_one_aquarium(db_env):
    _insert_fish(db_env, fish_id=1, fish_name="Goldfish")
    _insert_fish(db_env, fish_id=2, fish_name="Guppy")
    _insert_fish_in_aquarium(db_env, aquarium_id=1, fish_id=1, quantity=2)
    _insert_fish_in_aquarium(db_env, aquarium_id=1, fish_id=2, quantity=1)
    _insert_fish_in_aquarium(db_env, aquarium_id=2, fish_id=1, quantity=4)

    result = get_aquarium_fish(1)

    assert result == [("Goldfish", 2), ("Guppy", 1)]


def test_get_aquarium_fish_returns_empty_list_when_aquarium_has_no_fish(db_env):
    _insert_fish(db_env, fish_id=1, fish_name="Goldfish")

    result = get_aquarium_fish(42)

    assert result == []
