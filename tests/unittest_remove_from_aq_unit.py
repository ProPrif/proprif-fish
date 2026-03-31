# app/services/test_remove_fish_from_aquarium.py
import sqlite3
import pytest

from app.services import remove_fish_from_aquarium as service_module
from app.services.remove_fish_from_aquarium import (
    remove_fish_from_aquarium,
    recalculate_aquarium_balance,
)


def _init_schema(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE aquarium (
            id INTEGER PRIMARY KEY,
            volume INTEGER NOT NULL
        );

        CREATE TABLE fish_list (
            id INTEGER PRIMARY KEY,
            size INTEGER NOT NULL,
            aggression TEXT NOT NULL,
            temp_min REAL NOT NULL,
            temp_max REAL NOT NULL,
            ph_min REAL NOT NULL,
            ph_max REAL NOT NULL
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


def _insert_aquarium(db_path: str, aquarium_id: int, volume: int) -> None:
    _exec(
        db_path,
        "INSERT INTO aquarium (id, volume) VALUES (?, ?)",
        (aquarium_id, volume),
    )


def _insert_fish(
    db_path: str,
    fish_id: int,
    size: int,
    aggression: str = "CALM",
    temp_min: float = 24.0,
    temp_max: float = 28.0,
    ph_min: float = 6.5,
    ph_max: float = 7.5,
) -> None:
    _exec(
        db_path,
        """
        INSERT INTO fish_list (id, size, aggression, temp_min, temp_max, ph_min, ph_max)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (fish_id, size, aggression, temp_min, temp_max, ph_min, ph_max),
    )


def _insert_fish_in_aquarium(
    db_path: str, aquarium_id: int, fish_id: int, record_id: int | None = None
) -> None:
    if record_id is None:
        _exec(
            db_path,
            "INSERT INTO fish_in_aquarium (aquarium_id, fish_id) VALUES (?, ?)",
            (aquarium_id, fish_id),
        )
    else:
        _exec(
            db_path,
            "INSERT INTO fish_in_aquarium (id, aquarium_id, fish_id) VALUES (?, ?, ?)",
            (record_id, aquarium_id, fish_id),
        )


@pytest.fixture
def db_env(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test_remove_fish.sqlite3")
    _init_schema(db_path)
    monkeypatch.setattr(service_module, "APP_DB", db_path)
    monkeypatch.setattr(service_module, "ensure_tables", lambda: None)
    return db_path


def test_remove_first_matching_record_when_record_id_not_provided(db_env):
    _insert_aquarium(db_env, aquarium_id=1, volume=100)
    _insert_fish(db_env, fish_id=1, size=5)
    _insert_fish_in_aquarium(db_env, aquarium_id=1, fish_id=1, record_id=1)
    _insert_fish_in_aquarium(db_env, aquarium_id=1, fish_id=1, record_id=2)

    result = remove_fish_from_aquarium(aquarium_id=1, fish_id=1)

    assert result["success"] is True
    assert result["deleted_record_id"] == 1
    assert result["new_balance"] == "GREEN"
    assert _fetchall(db_env, "SELECT id FROM fish_in_aquarium ORDER BY id") == [(2,)]


def test_remove_specific_record_when_record_id_provided(db_env):
    _insert_aquarium(db_env, aquarium_id=1, volume=100)
    _insert_fish(db_env, fish_id=1, size=5)
    _insert_fish_in_aquarium(db_env, aquarium_id=1, fish_id=1, record_id=10)
    _insert_fish_in_aquarium(db_env, aquarium_id=1, fish_id=1, record_id=20)

    result = remove_fish_from_aquarium(aquarium_id=1, fish_id=1, record_id=20)

    assert result["success"] is True
    assert result["deleted_record_id"] == 20
    assert _fetchall(db_env, "SELECT id FROM fish_in_aquarium ORDER BY id") == [(10,)]


def test_remove_returns_error_when_fish_not_found(db_env):
    _insert_aquarium(db_env, aquarium_id=1, volume=100)
    _insert_fish(db_env, fish_id=1, size=5)

    result = remove_fish_from_aquarium(aquarium_id=1, fish_id=1)

    assert result == {"error": "Žuvis akvariume nerasta"}


def test_recalculate_returns_unknown_for_missing_aquarium(db_env):
    assert recalculate_aquarium_balance(999) == "UNKNOWN"


def test_recalculate_returns_empty_when_no_fish(db_env):
    _insert_aquarium(db_env, aquarium_id=1, volume=100)
    assert recalculate_aquarium_balance(1) == "EMPTY"


def test_recalculate_returns_red_when_volume_exceeded(db_env):
    _insert_aquarium(db_env, aquarium_id=1, volume=5)
    _insert_fish(db_env, fish_id=1, size=4)
    _insert_fish(db_env, fish_id=2, size=3)
    _insert_fish_in_aquarium(db_env, aquarium_id=1, fish_id=1)
    _insert_fish_in_aquarium(db_env, aquarium_id=1, fish_id=2)

    assert recalculate_aquarium_balance(1) == "RED"


def test_recalculate_returns_red_when_temperature_ranges_do_not_overlap(db_env):
    _insert_aquarium(db_env, aquarium_id=1, volume=100)
    _insert_fish(db_env, fish_id=1, size=2, temp_min=20, temp_max=22)
    _insert_fish(db_env, fish_id=2, size=2, temp_min=24, temp_max=26)
    _insert_fish_in_aquarium(db_env, aquarium_id=1, fish_id=1)
    _insert_fish_in_aquarium(db_env, aquarium_id=1, fish_id=2)

    assert recalculate_aquarium_balance(1) == "RED"


def test_recalculate_returns_red_when_ph_ranges_do_not_overlap(db_env):
    _insert_aquarium(db_env, aquarium_id=1, volume=100)
    _insert_fish(db_env, fish_id=1, size=2, ph_min=6.0, ph_max=6.4)
    _insert_fish(db_env, fish_id=2, size=2, ph_min=6.8, ph_max=7.2)
    _insert_fish_in_aquarium(db_env, aquarium_id=1, fish_id=1)
    _insert_fish_in_aquarium(db_env, aquarium_id=1, fish_id=2)

    assert recalculate_aquarium_balance(1) == "RED"


def test_recalculate_returns_yellow_when_aggressive_fish_present(db_env):
    _insert_aquarium(db_env, aquarium_id=1, volume=100)
    _insert_fish(db_env, fish_id=1, size=2, aggression="AGGRESSIVE")
    _insert_fish(db_env, fish_id=2, size=2, aggression="CALM")
    _insert_fish_in_aquarium(db_env, aquarium_id=1, fish_id=1)
    _insert_fish_in_aquarium(db_env, aquarium_id=1, fish_id=2)

    assert recalculate_aquarium_balance(1) == "YELLOW"


def test_recalculate_returns_green_when_all_conditions_are_compatible(db_env):
    _insert_aquarium(db_env, aquarium_id=1, volume=100)
    _insert_fish(db_env, fish_id=1, size=2, aggression="CALM", temp_min=24, temp_max=28, ph_min=6.5, ph_max=7.5)
    _insert_fish(db_env, fish_id=2, size=3, aggression="CALM", temp_min=25, temp_max=27, ph_min=6.8, ph_max=7.2)
    _insert_fish_in_aquarium(db_env, aquarium_id=1, fish_id=1)
    _insert_fish_in_aquarium(db_env, aquarium_id=1, fish_id=2)

    assert recalculate_aquarium_balance(1) == "GREEN"
